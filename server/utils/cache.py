#!/usr/bin/env python
# utils/cache.py

from django.core.cache import cache
from typing import Any, Optional

# -------------------------
# CHAT HISTORY

def get_user_consent_history(session_url: str) -> list[dict]:
    """Retrieve the full chat history for a given session."""
    return cache.get(f"history:{session_url}", [])


def set_user_consent_history(session_url: str, history: list[dict]) -> None:
    """Store the full chat history for a given session."""
    cache.set(f"history:{session_url}", history, timeout=None)


def append_to_consent_history(session_url: str, turn: dict) -> None:
    """Append a single turn to the chat history."""
    history = get_user_consent_history(session_url)
    history.append(turn)
    set_user_consent_history(session_url, history)

# -------------------------
# STATE FLAGS / METADATA

def set_flag(session_url: str, key: str, value: Any) -> None:
    """Set a temporary flag in the session cache."""
    state = cache.get(f"state:{session_url}", {})
    state[key] = value
    cache.set(f"state:{session_url}", state, timeout=None)


def get_flag(session_url: str, key: str) -> Optional[Any]:
    """Get a specific flag from the session cache."""
    state = cache.get(f"state:{session_url}", {})
    return state.get(key)


def clear_session_cache(session_url: str) -> None:
    """Clear all cached history and state for a session."""
    cache.delete(f"history:{session_url}")
    cache.delete(f"state:{session_url}")

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
