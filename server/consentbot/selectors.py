#!/usr/bin/env python
# consentbot/selectors.py

import uuid
from datetime import datetime
from typing import Optional
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from consentbot.models import (
    ConsentScript,
    ConsentSession,
)

User = get_user_model()

def get_latest_consent(user):
    return user.consents.order_by('-created_at').first()


from utils.cache import (
    get_user_consent_history,
    set_user_consent_history
)

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


def get_next_consent_sequence(
    conversation_graph: dict,
    node_id: str,
    skip_correct_test_nodes: bool = False,
    correct_questions: set[str] = None
) -> dict:
    """
    Traverses the conversation graph starting from `node_id` and collects:
    - Bot messages
    - User response options (if any)
    - Render info (form/button)
    - Whether the sequence ends
    - All node_ids visited during traversal

    Returns:
        dict: {
            "messages": list[str],
            "responses": list[{"id": str, "label": str}],
            "render": dict | None,
            "end": bool,
            "visited": list[str]
        }
    """
    visited = []
    messages = []
    responses = []
    current_id = node_id
    end = False
    render = None

    while True:
        node = conversation_graph.get(current_id, {})
        visited.append(current_id)
        if current_id == "VUipQHn":
            skip_correct_test_nodes = None
        
        # Check for skip if second test and node already answered correctly
        if skip_correct_test_nodes:
            test_node_id = infer_test_question_id(conversation_graph, current_id)
            if test_node_id in (correct_questions or set()):
                children = node.get("child_ids", [])
                if children:
                    current_id = children[0]
                    continue
                break

        if node.get("type") == "bot":
            messages.extend(node.get("messages", []))
            if str(node.get("metadata", {}).get("end_sequence", "false")).lower() == "true":
                end = True

            children = node.get("child_ids", [])
            if not children:
                break

            all_users = all(conversation_graph.get(cid, {}).get("type") == "user" for cid in children)
            if all_users:
                for cid in children:
                    if not skip_correct_test_nodes or (
                        infer_test_question_id(conversation_graph, cid) not in correct_questions
                    ):
                        responses.append({
                            "id": cid,
                            "label": get_user_label(conversation_graph[cid])
                        })
                        visited.append(cid)
                break
            elif len(children) == 1:
                current_id = children[0]
                continue
            break

        elif node.get("type") == "user":
            responses.append({
                "id": current_id,
                "label": get_user_label(node)
            })
            children = node.get("child_ids", [])
            if children:
                current_id = children[0]
                continue
            break

        else:
            break

    return {
        "messages": messages,
        "responses": responses,
        "render": node.get("render", None),
        "end": end,
        "visited": visited,
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
    *,
    speaker: str,
    node_id: str,
    messages: list[str],
    responses: Optional[list] = None
) -> dict:
    """
    Format a single chat turn for the consent chat history.

    Args:
        speaker (str): "user" or "bot"
        node_id (str): The node in the consent script this turn relates to.
        text (str): The message content (user reply or bot message).
        responses (list, optional): If this is a bot turn, include buttons or form fields.

    Returns:
        dict: A structured chat turn with metadata for storage and rendering.
    """
    return {
        "turn_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "speaker": speaker,
        "node_id": node_id,
        "messages": messages,
        "responses": responses or [],
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

from consentbot.models import ConsentSession

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
