#!/usr/bin/env python
# authentication/selectors.py

from django.shortcuts import get_object_or_404
from consentbot.models import ConsentScript
from authentication.models import UserConsent, UserConsentUrl
from utils.cache import (
    get_user_consent_history,
    get_user_workflow,
    set_user_consent_history
)
from utils.utility_functions import (
    get_consent_start_id,
    process_workflow,
)

from consentbot.selectors import (
    get_script_from_invite_id
)

def get_or_initialize_consent_history(invite_id):
    """
    Retrieve existing consent history for a given invite_id,
    or initialize it with the starting node and first chat sequence.

    Returns:
        tuple: (history, just_created)
    """
    history = get_user_consent_history(invite_id)
    if history:
        return history, False

    conversation_graph = get_script_from_invite_id(invite_id)
    start_node_id = get_consent_start_id(conversation_graph)
    first_sequence = process_workflow(start_node_id, invite_id)

    history = [{
        "node_id": start_node_id,  # ✅ Fix: add this
        "next_consent_sequence": first_sequence,
        "echo_user_response": ""
    }]

    set_user_consent_history(invite_id, history)
    return history, True


def get_user_from_invite(invite_id):
    """
    Retrieve the User instance associated with a given invite ID.
    """
    consent_url = get_object_or_404(UserConsentUrl, consent_url=invite_id)
    return consent_url.user

def get_consent_history(invite_id):
    """
    Retrieve the user's chat history from the cache.
    """
    return get_user_consent_history(invite_id)

def get_workflow(invite_id):
    """
    Retrieve the user's current workflow from the cache.
    """
    return get_user_workflow(invite_id)

def get_consent_names():
    return list(ConsentScript.objects.values_list('name', flat=True))

def get_max_version_number(consent_id):
    return (
        ConsentScript.objects
        .filter(derived_from_id=consent_id)
        .aggregate(models.Max('version_number'))['version_number__max']
        or 0
    )

def get_first_test_score(user):
    tests = user.user_tests.filter(test_try_num=1)
    total = tests.count()
    correct = tests.filter(answer_correct=True).count()
    if total == 0:
        return "NA"
    return f"{(correct / total) * 100:.0f}%"

def get_latest_consent(user):
    return user.user_consents.order_by('-created_at').first()
