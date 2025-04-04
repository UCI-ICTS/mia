#!/usr/bin/env python
# authentication/selectors.py

from consentbot.models import ConsentUrl, ConsentScript
from utils.cache import (
    get_user_consent_history,
    get_user_workflow,
)


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
