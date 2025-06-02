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

def set_flag(session_slug: str, key: str, value: Any) -> None:
    """Set a temporary flag in the session cache."""
    state = cache.get(f"state:{session_slug}", {})
    state[key] = value
    cache.set(f"state:{session_slug}", state, timeout=None)


def get_flag(session_slug: str, key: str) -> Optional[Any]:
    """Get a specific flag from the session cache."""
    state = cache.get(f"state:{session_slug}", {})
    return state.get(key)


def clear_session_cache(session_slug: str) -> None:
    """Clear all cached history and state for a session."""
    cache.delete(f"history:{session_slug}")
    cache.delete(f"state:{session_slug}")

# -------------------------
# WORKFLOW GRAPH STATE

def get_user_workflow(session_slug: str) -> list[list[str]]:
    """
    Retrieve the user's current workflow graph.
    Each sublist represents a sub-workflow (e.g., enrolling self, enrolling children).
    """
    return cache.get(f"workflow:{session_slug}", [])


def set_user_workflow(session_slug: str, workflow: list[list[str]]) -> None:
    """
    Store the user's current workflow graph.
    Each sublist represents a sub-workflow (sequence of node IDs).
    """
    cache.set(f"workflow:{session_slug}", workflow, timeout=None)
