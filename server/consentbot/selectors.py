#!/usr/bin/env python
# consentbot/selectors.py

import uuid
from typing import Optional
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from consentbot.models import (
    ConsentScript,
    ConsentSession,
    ConsentTestAttempt,
)

from utils.cache import (
    get_user_consent_history
)

User = get_user_model()

def get_latest_consent(user):
    return user.consents.order_by('-created_at').first()


def get_bot_messages(node):
    return node.get("messages", []) if node.get("type") == "bot" else []


def get_user_label(node: dict) -> str | dict:
    """
    Extracts a label from a user node for display as a response option.

    Args:
        node (dict): A node from the consent graph (expected to be of type 'user').

    Returns:
        str | dict:
            - If the node has messages, returns the first message (str).
            - If the node uses a form render, returns the full render block (dict).
            - Returns a fallback string if nothing is found.
    """
    messages = node.get("messages", [])
    if messages:
        return messages[0]

    render = node.get("render", {})
    if render.get("type") != "button":
        return render

    return "[Unknown response]"


def get_form_content(node: dict) -> dict | None:
    """
    Returns the form render block for a node if it's a form-type render.

    Args:
        node (dict): A node from the consent graph.

    Returns:
        dict | None: The full render block if it's a form, otherwise None.
    """
    render = node.get("render", {})
    return render if render.get("type") == "form" else None


def get_consent_start_id(graph):
    """Returns graph start"""
    for node_id, node in graph.items():
        if node.get("parent_ids") and node["parent_ids"][0] == "start":
            return node_id
    raise ValueError("Consent start node not found — check graph parent_ids")


def infer_test_question_id(graph: dict, node_id: str) -> str | None:
    """Walk upward from `node_id` to find the test question's bot node."""
    seen, queue = set(), [node_id]
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        node = graph.get(current, {})
        if node.get("metadata", {}).get("test_question") is True:
            return current
        queue.extend(node.get("parent_ids", []))
    return None


def get_next_retry_question_node(attempt) -> str | None:
    """
    Given a ConsentTestAttempt, return the next question node the user should retry,
    skipping questions they've already answered correctly.

    Args:
        attempt (ConsentTestAttempt): The current attempt.

    Returns:
        str | None: The next question node ID to retry, or None if done.
    """
    correct = set(attempt.answers.filter(answer_correct=True).values_list("question_node_id", flat=True))
    incorrect = attempt.answers.filter(answer_correct=False).values_list("question_node_id", flat=True)

    for qid in incorrect:
        if qid not in correct:
            return qid  # Retry this question

    return None  # All incorrect questions have been corrected


def traverse_consent_graph(conversation_graph:dict, node_id:str, session_slug:str=None)-> dict:
    """
    Traverses the graph starting at a bot node, collecting bot turns and user response options.
    Stops when a user node is reached or a decision point is found (e.g., fork in the graph).

    Returns:
        dict: {
            "chat_turns": [bot_turns...],
            "responses": [user response options],
            "render": render metadata (e.g., buttons, form),
            "end": bool (whether sequence is finished),
            "visited": [node_ids traversed]
        }
    """
    visited = []
    chat_turns = []
    responses = []
    current_id = node_id
    end = False
    render = None
    try:
        session = ConsentSession.objects.get(session_slug=session_slug)
        tries = session.user.num_test_tries
    except: 
        session = None
        tries = None
        
    while True:
        node = conversation_graph.get(current_id, {})
        visited.append(current_id)
        node_type = node.get("type")

        if node_type == "bot":
            if tries == 2 and node['metadata']['workflow'] == "test_user_understanding":
                attempt = ConsentTestAttempt.objects.filter(
                    user=session.user,
                    consent_script_version=session.script
                ).first()
                correct_ids = attempt.answers.filter(answer_correct=True).values_list("question_node_id", flat=True)
                if  current_id not in correct_ids:
                    turn = format_turn(
                        graph=conversation_graph,
                        speaker="bot",
                        node_id=current_id,
                        messages=node.get("messages", []),
                        render=node.get("render"),
                        end_sequence=node.get("metadata", {}).get("end_sequence", False)
                    )

                    chat_turns.append(turn)
                
                current_id = get_next_retry_question_node(attempt)
                node = conversation_graph.get(current_id, {})

            # Append formatted bot turn
            turn = format_turn(
                graph=conversation_graph,
                speaker="bot",
                node_id=current_id,
                messages=node.get("messages", []),
                render=node.get("render"),
                end_sequence=node.get("metadata", {}).get("end_sequence", False)
            )

            chat_turns.append(turn)

            # End of sequence?
            if str(node.get("metadata", {}).get("end_sequence", "false")).lower() == "true":
                end = True

            children = node.get("child_ids", [])
            if not children:
                break

            # If next step is a user response block
            if all(conversation_graph.get(cid, {}).get("type") == "user" for cid in children):
                # import pdb; pdb.set_trace()
                for cid in children:
                    user_node = conversation_graph.get(cid, {})
                    responses.append({
                        "id": cid,
                        "label": get_user_label(user_node),
                        "metadata": user_node.get("metadata", {})
                    })
                    visited.append(cid)
                render = node.get("render", {"type": "button"})
                break

            # Continue down a linear path
            if len(children) == 1:
                current_id = children[0]
                continue

            break  # Fork in the graph

        elif node_type == "user":
            responses.append({
                "id": current_id,
                "label": get_user_label(node),
                "metadata": node.get("metadata", {})
            })
            break

        else:
            break

    # Attach responses to the final bot turn
    if chat_turns:
        chat_turns[-1]["responses"] = responses
        chat_turns[-1]["render"] = render or {"type": "button"}

    # # Targeted fix: remove prior question if retry just restarted
    if (
        len(chat_turns) >= 2 and
        chat_turns[-1]["metadata"].get("test_question") is True and
        chat_turns[-2]["metadata"].get("test_question") is True and
        chat_turns[-1]["node_id"] != chat_turns[-2]["node_id"]
    ):
        # Only applies if they are different questions in the same test workflow
        chat_turns.pop(-2)

    return {
        "chat_turns": chat_turns,
        "responses": responses,
        "render": render,
        "end": end,
        "visited": visited
    }


def get_user_from_session_slug(session_slug: str):
    """
    Retrieve the User instance associated with a given invite ID.
    """
    session_slug = get_object_or_404(ConsentSession, session_slug=session_slug)
    return session_slug.user


def get_script_from_session_slug(session_slug: str) -> dict:
    """Retrieve the consent script JSON from a ConsentSession UUID."""
    try:
        script_id = ConsentSession.objects.get(session_slug=session_slug).user.consent_script_id
        if not script_id:
            raise ValidationError("User does not have a consent_script assigned.")
        return ConsentScript.objects.get(script_id=script_id).script
    except ConsentSession.DoesNotExist:
        raise NotFound(f"Invite ID {session_slug} not found.")
    except ConsentScript.DoesNotExist:
        raise NotFound(f"ConsentScript for invite ID {session_slug} not found.")


def format_turn(
    graph: dict,
    node_id: str,
    speaker: str,
    messages: list[str],
    responses: Optional[list] = None,
    render: Optional[dict] = None,
    end_sequence: bool = False,
    timestamp: Optional[str] = None
) -> dict:
    """
    Format a single chat turn to standard structure, including node metadata.

    Args:
        graph (dict): Full conversation graph (for accessing metadata).
        node_id (str): ID of the current node.
        speaker (str): 'bot' or 'user'.
        messages (list): Chat message(s) from speaker.
        responses (list, optional): Response options or form buttons.
        render (dict, optional): Render metadata block (form/button).
        end_sequence (bool): Whether this is the end of a sequence.
        timestamp (str, optional): ISO-formatted timestamp. Defaults to now.

    Returns:
        dict: Structured chat turn.
    """
    node_metadata = graph.get(node_id, {}).get("metadata", {})

    return {
        "speaker": speaker,
        "node_id": node_id,
        "messages": messages,
        "responses": responses or [],
        "render": render,
        "end_sequence": end_sequence,
        "timestamp": timestamp or timezone.now().isoformat(),
        "metadata": node_metadata
    }


def build_chat_from_history(session_slug: str) -> list[dict]:
    """
    Builds a list of completed chat turns for frontend consumption.

    Args:
        session_slug (str): The invite UUID identifying the session.

    Returns:
        list[dict]: A list of chat turn dictionaries (each with bot/user messages).
    """
    history = get_user_consent_history(session_slug)
    return [entry for entry in history if "messages" in entry]



def get_consent_session_or_error(session_slug: str) -> ConsentSession:
    """
    Retrieve a ConsentSession by slug or raise a ValueError.

    Args:
        session_slug (str): The session identifier slug.

    Returns:
        ConsentSession: The matching session object.

    Raises:
        ValueError: If no session is found.
    """
    try:
        return ConsentSession.objects.get(session_slug=session_slug)
    except ConsentSession.DoesNotExist:
        raise ValueError(f"No session found for slug: {session_slug}")
