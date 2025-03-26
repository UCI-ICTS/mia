#!/usr/bin/env python
# utils/cache.py

import json
from authentication.models import UserConsentCache


def _get_cache_value(key):
    try:
        user_consent_cache = UserConsentCache.objects.get(pk=key)
        return user_consent_cache.value
    except UserConsentCache.DoesNotExist:
        return None



def _set_cache_value(key, value):
    obj, _ = UserConsentCache.objects.get_or_create(pk=key)
    if isinstance(value, (dict, list)):
        obj.value = json.dumps(value)
    else:
        obj.value = str(value)
    obj.save()


def _build_key(invite_id, suffix):
    return f'invite_id:{invite_id}:{suffix}'


def get_user_workflow(invite_id):
    key = _build_key(invite_id, 'workflow')
    value = _get_cache_value(key)
    return json.loads(value) if value else None


def set_user_workflow(invite_id, workflow):
    key = _build_key(invite_id, 'workflow')
    _set_cache_value(key, json.dumps(workflow))


def set_consenting_myself(invite_id, consenting=True):
    key = _build_key(invite_id, 'user_consenting')
    _set_cache_value(key, consenting)


def get_consenting_myself(invite_id):
    key = _build_key(invite_id, 'user_consenting')
    value = _get_cache_value(key)
    return value == 'true' if value else None


def set_consenting_children(invite_id, consenting=True):
    key = _build_key(invite_id, 'children_consenting')
    _set_cache_value(key, consenting)


def get_consenting_children(invite_id):
    key = _build_key(invite_id, 'children_consenting')
    value = _get_cache_value(key)
    return value == 'true' if value else None


def set_consent_node(invite_id, consent_node_id):
    key = _build_key(invite_id, 'consent_node_id')
    _set_cache_value(key, consent_node_id)


def get_consent_node(invite_id):
    key = _build_key(invite_id, 'consent_node_id')
    value = _get_cache_value(key)
    return value if value else None


def set_child_user_id(invite_id, child_user_id):
    key = _build_key(invite_id, 'child_user_id')
    _set_cache_value(key, child_user_id)


def get_child_user_id(invite_id):
    key = _build_key(invite_id, 'child_user_id')
    value = _get_cache_value(key)
    return value if value else None


def get_child_user_consent_id(invite_id):
    key = _build_key(invite_id, 'child_user_consent_id')
    return _get_cache_value(key)


def set_child_user_consent_id(invite_id, child_user_consent_id):
    key = _build_key(invite_id, 'child_user_consent_id')
    _set_cache_value(key, child_user_consent_id)


def get_user_consent_history(invite_id):
    key = _build_key(invite_id, 'user_consent_history')
    value = _get_cache_value(key)
    return json.loads(value) if value else []


def set_user_consent_history(invite_id, user_consent_history):
    key = _build_key(invite_id, 'user_consent_history')
    _set_cache_value(key, json.dumps(user_consent_history))
