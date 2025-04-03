#!/usr/bin/env python
# consentbot/serializers.py

from rest_framework import serializers
from django.shortcuts import get_object_or_404
from consentbot.models import ConsentScript
from authentication.models import (
    UserConsent,
    UserConsentUrl
)
from consentbot.selectors import (
    build_chat_from_history,
    format_turn,
    get_script_from_invite_id,
)
from utils.utility_functions import (
    clean_up_after_chat,
    process_workflow,
    generate_workflow,
)
from utils.cache import (
    get_user_consent_history,
    set_user_consent_history
)

class ConsentInputSerializer(serializers.ModelSerializer):
    derived_from = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = ConsentScript
        fields = ['name', 'description', 'derived_from', 'script']

class ConsentOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentScript
        fields = ['consent_id', 'name', 'description', 'version_number', 'script', 'created_at']


def append_chat_history(invite_id:str, chat_turn:dict):
    """
    Appends a chat turn to the user's consent chat history in cache.

    Args:
        invite_id (str): The invite UUID identifying the session.
        chat_turn (dict): A formatted chat turn dictionary using `format_turn`.
    """
    history = get_user_consent_history(invite_id)
    history.append(chat_turn)
    set_user_consent_history(invite_id, history)


def handle_user_feedback_form(invite_id, responses):
    """
    Handles submission of a feedback form, stores the data,
    and advances the chat sequence.

    Args:
        invite_id (str): The invite UUID identifying the session.
        responses (list): List of form response dicts.

    Returns:
        list[dict]: Updated chat history for the frontend.
    """
    from authentication.services import UserFeedbackInputSerializer

    response_dict = {r.get("name"): r.get("value") for r in responses if r.get("name")}
    node_id = response_dict.get("node_id")
    if not node_id:
        raise ValueError("Missing node ID")

    feedback_data = {
        "satisfaction": response_dict.get("satisfaction", ""),
        "suggestions": (response_dict.get("suggestions") or "")[:2000]
    }

    consent_url = get_object_or_404(UserConsentUrl, consent_url=invite_id)
    if response_dict.get('anonymize') is None:
        feedback_data["user"] = consent_url.user.pk

    serializer = UserFeedbackInputSerializer(data=feedback_data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    conversation_graph = get_script_from_invite_id(invite_id)
    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_workflow(next_node_id, invite_id)

    append_chat_history(invite_id, format_turn(
        conversation_graph, node_id, "Feedback submitted!", next_sequence
    ))

    clean_up_after_chat(invite_id)
    return build_chat_from_history(invite_id)


def handle_sample_storage(conversation_graph:dict, invite_id:str, responses:list):
    """
    Processes the 'sample storage' form by updating the user's consent record,
    saving chat state, and progressing the conversation.

    Args:
        conversation_graph (dict): The full consent script graph.
        invite_id (str): The invite UUID identifying the session.
        responses (list): List of form response dicts.

    Returns:
        list[dict]: Updated chat history for the frontend.
    """
    samples = responses[0]['value']
    node_id = responses[1]['value']

    user = UserConsentUrl.objects.get(consent_url=invite_id).user
    consent = UserConsent.objects.filter(user=user).order_by('-created_at').first()

    consent.store_sample_this_study = True
    consent.store_sample_other_studies = (samples == "storeSamplesOtherStudies")
    consent.save()

    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_workflow(next_node_id, invite_id)

    append_chat_history(invite_id, format_turn(
        conversation_graph, node_id, "Sample use submitted!", next_sequence
    ))

    clean_up_after_chat(invite_id)
    return build_chat_from_history(invite_id)


def handle_phi_use(conversation_graph, invite_id, responses):
    """
    Handles the form submission for PHI (Protected Health Information) usage consent.

    Updates the user's `UserConsent` object to reflect their PHI usage choices and 
    appends the next sequence of the chat to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """
    samples = responses[0]['value']
    node_id = responses[1]['value']

    user = UserConsentUrl.objects.get(consent_url=invite_id).user
    consent = UserConsent.objects.filter(user=user).order_by('-created_at').first()
    consent.store_phi_this_study = True
    consent.store_phi_other_studies = (samples == "storePhiOtherStudies")
    consent.save()

    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_workflow(next_node_id, invite_id)

    echo_user_response = "PHI use submitted!"
    history = get_user_consent_history(invite_id)
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)
    clean_up_after_chat(invite_id)

    return [
        {
            "node_id": entry.get("node_id", ""),
            "echo_user_response": entry.get("echo_user_response"),
            **entry.get("next_consent_sequence", {})
        }
        for entry in history if "next_consent_sequence" in entry
    ]


def handle_result_return(conversation_graph, invite_id, responses):
    """
    Handles the form submission for return of genetic results preferences.

    Updates the user's `UserConsent` object with their selected options and appends
    the next chat turn to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """
    response_dict = {r.get("name"): r.get("value") for r in responses if r.get("name")}
    node_id = response_dict["node_id"]

    user = UserConsentUrl.objects.get(consent_url=invite_id).user
    consent = UserConsent.objects.filter(user=user).order_by('-created_at').first()
    consent.return_primary_results = response_dict.get("rorPrimary") is True
    consent.return_actionable_secondary_results = response_dict.get("rorSecondary") is True
    consent.return_secondary_results = response_dict.get("rorSecondaryNot") is True
    consent.save()

    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_workflow(next_node_id, invite_id)

    echo_user_response = "Result return preferences submitted!"
    history = get_user_consent_history(invite_id)
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)
    clean_up_after_chat(invite_id)

    return [
        {
            "node_id": entry.get("node_id", ""),
            "echo_user_response": entry.get("echo_user_response"),
            **entry.get("next_consent_sequence", {})
        }
        for entry in history if "next_consent_sequence" in entry
    ]


def handle_consent(conversation_graph, invite_id, responses):
    """
    Handles the final user consent form submission.

    Stores the user's name, timestamps the consent, and marks the consent
    as complete. Also updates chat history with the next sequence.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """
    response_dict = {r.get("name"): r.get("value") for r in responses if r.get("name")}
    node_id = response_dict["node_id"]

    user = UserConsentUrl.objects.get(consent_url=invite_id).user
    consent = UserConsent.objects.filter(user=user).order_by('-created_at').first()

    if response_dict.get("consent") is True:
        consent.user_full_name_consent = response_dict.get("fullname", "")
        consent.consented_at = timezone.now()
        user.consent_complete = True
        user.save()
        consent.save()

    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_workflow(next_node_id, invite_id)

    echo_user_response = "Consent submitted!"
    history = get_user_consent_history(invite_id)
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)
    clean_up_after_chat(invite_id)

    return [
        {
            "node_id": entry.get("node_id", ""),
            "echo_user_response": entry.get("echo_user_response"),
            **entry.get("next_consent_sequence", {})
        }
        for entry in history if "next_consent_sequence" in entry
    ]

def handle_family_enrollment_form(conversation_graph, invite_id, responses):
    """
    Handles the form submission where the user indicates who they are enrolling (self, children, or both).

    Based on the checked options, this function:
    - Updates the user's enrollment flags.
    - Generates a dynamic sub-workflow for each selection.
    - Adds the next sequence to the consent chat history.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """
    checked_checkboxes = responses[0]["value"]
    checkbox_workflow_ids = []
    user = UserConsentUrl.objects.get(consent_url=invite_id).user
    # import pdb; pdb.set_trace()
    # Get latest history to find the node that generated this form
    history = get_user_consent_history(invite_id)
    parent_node_id = history[-1]['node_id'] if history else None

    if not parent_node_id or parent_node_id not in conversation_graph:
        raise Exception("Invalid or missing parent node")

    try:
        fields = history[-1]['user_responses'][0]['label']['fields']
    except Exception:
        raise Exception("Checkbox fields missing from chat history")

    # Create a lookup of checkbox values to child node IDs
    checkbox_node_ids = {field['name']: field['id_value'] for field in fields}

    for item in checked_checkboxes:
        if item in checkbox_node_ids:
            checkbox_workflow_ids.append(checkbox_node_ids[item])
            if item == "myself":
                user.enrolling_myself = True
            elif item == "myChildChildren":
                user.enrolling_children = True
        else:
            print(f"{item} not in checkbox_node_ids")

    user.save()

    # Start dynamic sub-workflow based on selected options
    start_node_id = checkbox_workflow_ids[0]
    generate_workflow(start_node_id, checkbox_workflow_ids, invite_id)
    next_sequence = process_workflow(start_node_id, invite_id)
    echo_user_response = ", ".join(checked_checkboxes)

    history.append(format_turn(conversation_graph, start_node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)

    return [
        {
            "node_id": entry.get("node_id", ""),
            "echo_user_response": entry.get("echo_user_response"),
            **entry.get("next_consent_sequence", {})
        }
        for entry in history if "next_consent_sequence" in entry
    ]
