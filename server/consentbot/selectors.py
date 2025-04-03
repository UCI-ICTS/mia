#!/usr/bin/env python
# consentbot/selectors.py

from authentication.models import (
    UserConsent,
    UserConsentUrl,
)
from consentbot.models import ConsentScript
from utils.cache import get_user_consent_history

def get_script_from_invite_id(invite_id):
    """Retrieve the consent script JSON from a UserConsentUrl UUID."""
    try:
        consent_id = UserConsentUrl.objects.get(consent_url=invite_id).user.consent_script_id
        if not consent_id:
            raise ValueError("User does not have a consent_script assigned.")
        return ConsentScript.objects.get(consent_id=consent_id).script
    except UserConsentUrl.DoesNotExist:
        raise ValueError(f"Invite ID {invite_id} not found.")
    except ConsentScript.DoesNotExist:
        raise ValueError(f"ConsentScript for invite ID {invite_id} not found.")

def format_turn(conversation_graph:dict, node_id:str, echo_user_response="", next_sequence:dict=None):
    """
    Formats a single chat turn to be stored in user chat history and returned to the frontend.

    Args:
        conversation_graph (dict): The full graph structure for the consent script.
        node_id (str): The ID of the current node (where the user submitted a response).
        echo_user_response (str, optional): The user's answer or input to be echoed back. Defaults to "".
        next_sequence (dict, optional): The next bot response block, as returned by `process_workflow`.

    Returns:
        dict: A dictionary representing a complete chat turn with:
            - node_id
            - echo_user_response
            - bot_messages
            - user_responses
            - user_render_type
            - render_type
            - render_content
            - end_sequence
    """
    node = conversation_graph.get(node_id, {})
    print("Render type: ", node.get("render_type", ""))
    return {
        "node_id": node_id,
        "echo_user_response": echo_user_response,
        "bot_messages": next_sequence.get("bot_messages", []) if next_sequence else [],
        "user_responses": next_sequence.get("user_responses", []) if next_sequence else [],
        "user_render_type": next_sequence.get("user_render_type", "button") if next_sequence else "button",
        "render_content": node.get("render_content", None),
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