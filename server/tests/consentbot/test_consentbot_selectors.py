#!/usr/bin/env python
# tests/consentbot/test_consentbot_selectors.py

from django.test import TestCase
from consentbot.models import ConsentUrl, ConsentScript, Consent
from consentbot.selectors import (
    get_latest_consent,
    get_bot_messages,
    get_user_label,
    get_form_content,
    get_consent_start_id,
    get_next_consent_sequence,
    get_user_from_invite_id,
    get_script_from_invite_id,
    format_turn,
    build_chat_from_history,
)
from utils.cache import set_user_consent_history
import uuid


class SelectorFunctionTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.invite = ConsentUrl.objects.first()
        self.user = self.invite.user
        self.script = self.user.consent_script
        self.graph = self.script.script

    def test_get_latest_consent(self):
        # import pdb; pdb.set_trace()
        consent = get_latest_consent(self.user)
        self.assertIsInstance(consent, Consent)

    def test_get_user_from_invite_id(self):
        user = get_user_from_invite_id(str(self.invite.consent_url))
        self.assertEqual(user.pk, self.user.pk)

    def test_get_script_from_invite_id(self):
        graph = get_script_from_invite_id(str(self.invite.consent_url))
        self.assertIsInstance(graph, dict)
        self.assertIn("start", graph)

    def test_get_next_consent_sequence_returns_messages(self):
        sequence = get_next_consent_sequence(self.graph, "start")
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
        seq = get_next_consent_sequence(self.graph, "start")
        turn = format_turn(self.graph, "start", echo_user_response="Yes", next_sequence=seq)
        self.assertIn("messages", turn)
        self.assertIn("responses", turn)

    def test_build_chat_from_history(self):
        sample = [{"node_id": "start", "messages": ["Hi!"]}]
        set_user_consent_history(str(self.invite.consent_url), sample)
        history = build_chat_from_history(str(self.invite.consent_url))
        self.assertEqual(history, sample)
