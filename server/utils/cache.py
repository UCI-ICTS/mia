#!/usr/bin/env python
# utils/cache.py

from typing import Any, Optional
from django.utils import timezone
from django.core.cache import cache
from consentbot.models import ConsentChatTurn, ConsentSession

# -------------------------
# CHAT HISTORY


def get_user_consent_history(session_slug: str) -> list[dict]:
    session = ConsentSession.objects.get(session_slug=session_slug)
    return [turn.node for turn in session.chat_turns.all()]


def set_user_consent_history(session_slug: str, history: list[dict]) -> None:
    session = ConsentSession.objects.get(session_slug=session_slug)
    session.chat_turns.all().delete()
    for turn in history:
        ConsentChatTurn.objects.create(
            session=session,
            user=session.user,
            node_id=turn["node_id"],
            node=turn,
            timestamp=turn.get("timestamp", timezone.now())
        )


def append_to_consent_history(session_slug: str, turn: dict) -> None:
    session = ConsentSession.objects.get(session_slug=session_slug)
    ConsentChatTurn.objects.create(
        session=session,
        user=session.user,
        node_id=turn["node_id"],
        node=turn,
        timestamp=turn.get("timestamp", timezone.now())
    )


# -------------------------
# STATE FLAGS / METADATA

DEFAULT_STATE_TTL_SECONDS = 60 * 60 * 6  # 6 hours, adjust

def _state_key(session_slug: str) -> str:
    return f"state:{session_slug}"

def get_state(session_slug: str) -> dict:
    return cache.get(_state_key(session_slug), {}) or {}

def set_state(session_slug: str, state: dict, ttl: int = DEFAULT_STATE_TTL_SECONDS) -> None:
    cache.set(_state_key(session_slug), state, timeout=ttl)

def set_flag(session_slug: str, key: str, value: Any, ttl: int = DEFAULT_STATE_TTL_SECONDS) -> None:
    state = get_state(session_slug)
    state[key] = value
    set_state(session_slug, state, ttl=ttl)

def get_flag(session_slug: str, key: str) -> Optional[Any]:
    state = get_state(session_slug)
    return state.get(key)

def pop_flag(session_slug: str, key: str, default: Any = None) -> Any:
    state = get_state(session_slug)
    value = state.pop(key, default)
    if value == None:
        return False
    set_state(session_slug, state)
    return value

def delete_flag(session_slug: str, key: str) -> None:
    state = get_state(session_slug)
    if key in state:
        del state[key]
        set_state(session_slug, state)

def clear_session_cache(session_slug: str) -> None:
    cache.delete(_state_key(session_slug))