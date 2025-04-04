#!/usr/bin/env python
# consentbot/selectors.py

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from consentbot.models import (
    ConsentScript,
    ConsentUrl,
)

User = get_user_model()

from utils.cache import (
    get_user_consent_history,
    set_user_consent_history
)

def get_bot_messages(node):
    return node.get("messages", []) if node.get("type") == "bot" else []


def get_user_label(node: dict):
    messages = node.get("messages", [])
    if messages:
        return messages[0]
    
    if node.get("render_type") != "button": #and node.get("render_content"):
        return node["render_content"]  # Return the full form object

    return "[Unknown response]"


def get_form_content(node):
    return node.get("render_content") if node.get("render_type") == "form" else None


def get_consent_start_id(graph):
    for node_id, node in graph.items():
        if node.get("parent_ids") and node["parent_ids"][0] == "start":
            return node_id
    raise ValueError("Consent start node not found — check graph parent_ids")


def get_next_consent_sequence(conversation_graph, node_id):
    """
    Collects the next bot message sequence and corresponding user response options 
    starting from a given node_id. Returns a structured dict and the list of traversed node_ids.

    Args:
        conversation_graph (dict): The full conversation graph.
        node_id (str): The node to begin traversal from.

    Returns:
        tuple:
            - dict: Contains bot_messages, user_responses, render_type, render_content, end_sequence
            - list: All node_ids traversed in this sequence
    """

    bot_messages = []
    user_responses = []
    node_ids = []
    current_id = node_id
    user_render_type = "button"
    end_sequence = False

    while True:
        node = conversation_graph.get(current_id, {})
        node_ids.append(current_id)

        if node["type"] == "bot":
            bot_messages.extend(get_bot_messages(node))
            if node.get("metadata", {}).get("end_sequence") == "true":
                end_sequence = True
            child_ids = node.get("child_ids", [])
            if not child_ids:
                break
            # 👉 Look ahead: are all child nodes of type 'user'?
            all_children_are_users = all(
                conversation_graph.get(cid, {}).get("type") == "user" for cid in child_ids
            )
            if all_children_are_users:
                # Collect all user response options
                for cid in child_ids:
                    child_node = conversation_graph.get(cid, {})
                    user_render_type = child_node['render_type']
                    user_responses.append({
                        "id": cid,
                        "label": get_user_label(child_node)
                    })
                    node_ids.append(cid)
                break
            # If not all users, keep walking
            if len(child_ids) == 1:
                current_id = child_ids[0]
            else:
                break

        elif node["type"] == "user":
            user_responses.append({
                "id": current_id,
                "label": get_user_label(node)
            })
            break

        else:
            break

    return {
        "bot_messages": bot_messages,
        "user_responses": user_responses,
        "render_type": node.get("render_type", "button"),
        "render_content": node.get("render_content"),
        "user_render_type": user_render_type,
        "end_sequence": end_sequence,
    }, node_ids


def get_user_from_invite_id(invite_id: str):
    """
    Retrieve the User instance associated with a given invite ID.
    """
    consent_url = get_object_or_404(ConsentUrl, consent_url=invite_id)
    return consent_url.user


def get_script_from_invite_id(invite_id: str)-> str:
    """Retrieve the consent script JSON from a ConsentUrl UUID."""
    try:
        script_id = ConsentUrl.objects.get(consent_url=invite_id).user.consent_script_id
        if not script_id:
            raise ValueError("User does not have a consent_script assigned.")
        return ConsentScript.objects.get(script_id=script_id).script
    except ConsentUrl.DoesNotExist:
        raise ValueError(f"Invite ID {invite_id} not found.")
    except ConsentScript.DoesNotExist:
        raise ValueError(f"ConsentScript for invite ID {invite_id} not found.")


def format_turn(conversation_graph: dict, node_id: str, echo_user_response="", next_sequence: dict = None):
    """
    Formats a single chat turn to be stored in user chat history and returned to the frontend.

    Args:
        conversation_graph (dict): The full graph structure for the consent script.
        node_id (str): The ID of the current node (where the user submitted a response).
        echo_user_response (str, optional): The user's answer or input to be echoed back. Defaults to "".
        next_sequence (dict, optional): The next bot response block, as returned by `process_consent_sequence`.

    Returns:
        dict: A dictionary representing a complete chat turn with:
            - node_id
            - echo_user_response
            - bot_messages
            - user_responses
            - render_type
            - render_content
            - end_sequence
    """
    node = conversation_graph.get(node_id, {})

    return {
        "node_id": node_id,
        "echo_user_response": echo_user_response,
        "bot_messages": next_sequence.get("bot_messages", []) if next_sequence else [],
        "user_responses": next_sequence.get("user_responses", []) if next_sequence else [],
        "render_type": next_sequence.get("render_type", node.get("render_type", "button")),
        "user_render_type":next_sequence.get("user_render_type", "test"),
        "render_content": next_sequence.get("render_content", node.get("render_content")),
        "end_sequence": next_sequence.get("end_sequence", False) if next_sequence else False,
    }


def build_chat_from_history(invite_id:str)-> dict:
    """
    Builds a list of completed chat turns for frontend consumption.

    Args:
        invite_id (str): The invite UUID identifying the session.

    Returns:
        list[dict]: A list of chat turn dictionaries (each with bot/user messages).
    """
    history = get_user_consent_history(invite_id)
    return [entry for entry in history if "bot_messages" in entry]
