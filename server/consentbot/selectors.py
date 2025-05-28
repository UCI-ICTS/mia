#!/usr/bin/env python
# consentbot/selectors.py

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from consentbot.models import (
    ConsentScript,
    ConsentUrl,
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


def get_user_from_invite_id(invite_id: str):
    """
    Retrieve the User instance associated with a given invite ID.
    """
    consent_url = get_object_or_404(ConsentUrl, consent_url=invite_id)
    return consent_url.user


def get_script_from_invite_id(invite_id: str) -> dict:
    """Retrieve the consent script JSON from a ConsentUrl UUID."""
    try:
        script_id = ConsentUrl.objects.get(consent_url=invite_id).user.consent_script_id
        if not script_id:
            raise ValidationError("User does not have a consent_script assigned.")
        return ConsentScript.objects.get(script_id=script_id).script
    except ConsentUrl.DoesNotExist:
        raise NotFound(f"Invite ID {invite_id} not found.")
    except ConsentScript.DoesNotExist:
        raise NotFound(f"ConsentScript for invite ID {invite_id} not found.")



def format_turn(
    conversation_graph: dict,
    node_id: str,
    echo_user_response: str = "",
    next_sequence: dict | None = None
) -> dict:
    """
    Format a single chat turn in the consent conversation flow.

    Args:
        conversation_graph (dict): The full JSON-based consent graph.
        node_id (str): The node the user just responded to.
        echo_user_response (str, optional): Text representation of the user's input. Defaults to "".
        next_sequence (dict, optional): Output from `get_next_consent_sequence()`. If not provided,
                                        it falls back to values from `conversation_graph[node_id]`.

    Returns:
        dict: A chat turn formatted for frontend display and history tracking. Contains:
            - node_id: The node being answered
            - echo_user_response: What the user said or selected
            - messages: Bot messages
            - responses: User response options (buttons or form)
            - render: Render info (form config or button group)
            - end: Whether this ends the sequence
    """
    node = conversation_graph.get(node_id, {})

    # Prefer data from the graph unless rendering a special next_sequence node
    messages = node.get("messages", [])
    responses = node.get("responses", [])
    render = node.get("render")
    end = node.get("metadata", {}).get("end_sequence", False)
    
    if next_sequence:
        # This is only valid when formatting a bot response *after* get_next_consent_sequence
        messages = next_sequence.get("messages", messages)
        responses = next_sequence.get("responses", responses)
        render = next_sequence.get("render", render)
        end = next_sequence.get("end", end)

    return {
        "node_id": node_id,
        "echo_user_response": echo_user_response,
        "messages": messages,
        "responses": responses,
        "render": render,
        "end": end,
    }


def build_chat_from_history(invite_id: str) -> list[dict]:
    """
    Builds a list of completed chat turns for frontend consumption.

    Args:
        invite_id (str): The invite UUID identifying the session.

    Returns:
        list[dict]: A list of chat turn dictionaries (each with bot/user messages).
    """
    history = get_user_consent_history(invite_id)
    return [entry for entry in history if "messages" in entry]

