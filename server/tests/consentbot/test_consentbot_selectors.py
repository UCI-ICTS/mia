#!/usr/bin/env python
# tests/consentbot/test_consentbot_selectors.py

from django.test import TestCase
from consentbot.models import ConsentSession, ConsentScript, Consent
from consentbot.selectors import (
    get_latest_consent,
    get_bot_messages,
    get_user_label,
    get_form_content,
    get_consent_start_id,
    traverse_consent_graph,
    get_user_from_session_slug,
    get_script_from_session_slug,
    format_turn,
    build_chat_from_history,
)
from utils.cache import set_user_consent_history
import uuid


class SelectorFunctionTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.invite = ConsentSession.objects.first()
        self.user = self.invite.user
        self.script = self.user.consent_script
        self.graph = self.script.script

    def test_get_latest_consent(self): 
        consent = get_latest_consent(self.user)
        self.assertIsInstance(consent, Consent)

    def test_get_user_from_session_slug(self):
        user = get_user_from_session_slug(str(self.invite.session_slug))
        self.assertEqual(user.pk, self.user.pk)

    def test_get_script_from_session_slug(self):
        graph = get_script_from_session_slug(str(self.invite.session_slug))
        self.assertIsInstance(graph, dict)
        self.assertIn("start", graph)

    def test_traverse_consent_graph_returns_messages(self):
        sequence = traverse_consent_graph(self.graph, "start")
        self.assertIn("messages", sequence)
        self.assertIn("visited", sequence)

    def test_get_user_label_from_user_node(self):
        user_node = {
            "type": "user",
            "messages": ["Yes"],
            "render": {"type": "button"}
        }
        label = get_user_label(user_node)
        self.assertEqual(label, "Yes")

    def test_get_form_content_returns_form(self):
        node = {"render": {"type": "form", "fields": []}}
        form = get_form_content(node)
        self.assertEqual(form["type"], "form")

    def test_get_consent_start_id(self):
        start = get_consent_start_id(self.graph)
        self.assertIsInstance(start, str)

    def test_format_turn_output(self):
        turn = format_turn(self.graph, "start", "bot", [])
        self.assertIn("messages", turn)
        self.assertIn("responses", turn)

    def test_build_chat_from_history(self):
        sample = [{"node_id": "start", "messages": ["Hi!"]}]
        set_user_consent_history(str(self.invite.session_slug), sample)
        history = build_chat_from_history(str(self.invite.session_slug))
        self.assertEqual(history, sample)
