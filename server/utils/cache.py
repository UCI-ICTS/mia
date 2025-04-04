#!/usr/bin/env python
# utils/cache.py

import json
from consentbot.models import ConsentCache


# Internal helpers
def _cache_get(key):
    try:
        return ConsentCache.objects.get(pk=key).value
    except ConsentCache.DoesNotExist:
        return None


def _cache_set(key, value):
    obj, _ = ConsentCache.objects.get_or_create(pk=key)
    if isinstance(value, (dict, list)):
        obj.value = json.dumps(value)
    else:
        obj.value = str(value)
    obj.save()


def _build_key(invite_id, suffix):
    return f"invite_id:{invite_id}:{suffix}"


# Workflow
def get_user_workflow(invite_id):
    """Retrieve the user's current workflow graph (list of node ID lists)."""
    value = _cache_get(_build_key(invite_id, "workflow"))
    return json.loads(value) if value else []


def set_user_workflow(invite_id, workflow):
    """Store the user’s current workflow graph."""
    _cache_set(_build_key(invite_id, "workflow"), json.dumps(workflow))


# Consent status flags
def set_consenting_myself(invite_id, consenting=True):
    """Set whether the user is enrolling themselves."""
    _cache_set(_build_key(invite_id, "user_consenting"), consenting)


def get_consenting_myself(invite_id):
    """Get whether the user is enrolling themselves."""
    value = _cache_get(_build_key(invite_id, "user_consenting"))
    return value == "true" if value else None


def set_consenting_children(invite_id, consenting=True):
    """Set whether the user is enrolling children."""
    _cache_set(_build_key(invite_id, "children_consenting"), consenting)


def get_consenting_children(invite_id):
    """Get whether the user is enrolling children."""
    value = _cache_get(_build_key(invite_id, "children_consenting"))
    return value == "true" if value else None


# Consent chat node tracking
def set_consent_node(invite_id, consent_node_id):
    """Set the ID of the main consent node used during enrollment."""
    _cache_set(_build_key(invite_id, "consent_node_id"), consent_node_id)


def get_consent_node(invite_id):
    """Get the ID of the main consent node."""
    return _cache_get(_build_key(invite_id, "consent_node_id"))


# Child user tracking (for family enrollment)
def set_child_user_id(invite_id, child_user_id):
    """Store the user ID of a child participant."""
    _cache_set(_build_key(invite_id, "child_user_id"), child_user_id)


def get_child_user_id(invite_id):
    """Retrieve the user ID of a child participant."""
    return _cache_get(_build_key(invite_id, "child_user_id"))


def set_child_user_consent_id(invite_id, child_user_consent_id):
    """Store the consent record ID for a child participant."""
    _cache_set(_build_key(invite_id, "child_user_consent_id"), child_user_consent_id)


def get_child_user_consent_id(invite_id):
    """Retrieve the consent record ID for a child participant."""
    return _cache_get(_build_key(invite_id, "child_user_consent_id"))


# Chat history
def set_user_consent_history(invite_id, history):
    """Store the user’s full consent chat history (list of formatted turns)."""
    _cache_set(_build_key(invite_id, "user_consent_history"), json.dumps(history))


def get_user_consent_history(invite_id):
    """Retrieve the user’s full consent chat history."""
    value = _cache_get(_build_key(invite_id, "user_consent_history"))
    return json.loads(value) if value else []
