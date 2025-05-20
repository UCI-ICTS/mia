#!/usr/bin/env python
# tests/consentbot/test_consentbot_services.py

from django.test import TestCase
from consentbot.models import Consent, ConsentUrl
from consentbot.services import (
    handle_consent,
    handle_family_enrollment_form,
    handle_user_feedback_form,
    handle_other_adult_contact_form,
    update_consent_and_advance
)
from utils.cache import set_user_consent_history
from consentbot.selectors import get_script_from_invite_id
import uuid


class ConsentServiceTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.invite = ConsentUrl.objects.first()
        self.user = self.invite.user
        self.script = self.user.consent_script
        self.graph = self.script.script
        self.invite_id = str(self.invite.consent_url)

    def test_handle_consent_sets_flags_and_returns_chat(self):
        responses = [
            {"name": "node_id", "value": "start"},
            {"name": "consent", "value": "true"},
            {"name": "fullname", "value": "Jane Tester"}
        ]
        result = handle_consent(self.graph, self.invite_id, responses)
        self.assertIsInstance(result, list)
        self.user.refresh_from_db()
        self.assertTrue(self.user.consent_complete)
        consent = Consent.objects.filter(user=self.user).latest("created_at")
        self.assertEqual(consent.user_full_name_consent, "Jane Tester")

    def test_handle_family_enrollment_form_processes_workflow(self):
        history = [{
            "node_id": "b5nYNf6",
            "responses": [{
                "label": {
                    "fields": [
                        {"name": "myself", "id_value": "eca6cQF"},
                        {"name": "myChildChildren", "id_value": "RMb2hrx"}
                    ]
                }
            }]
        }]
        set_user_consent_history(self.invite_id, history)
        responses = [{"value": ["myself", "myChildChildren"]}]
        result = handle_family_enrollment_form(self.graph, self.invite_id, responses)
        self.assertIsInstance(result, list)
        self.user.refresh_from_db()
        self.assertTrue(self.user.enrolling_myself)
        self.assertTrue(self.user.enrolling_children)

    def test_handle_user_feedback_form_validates_and_saves(self):
        responses = [
            {"name": "node_id", "value": "start"},
            {"name": "satisfaction", "value": "Satisfied"},
            {"name": "suggestions", "value": "No issues."}
        ]
        result = handle_user_feedback_form(self.graph, self.invite_id, responses)
        self.assertIsInstance(result, list)

    def test_handle_other_adult_contact_form_progresses_chat(self):
        responses = [
            {"name": "node_id", "value": "start"},
            {"name": "full_name", "value": "John Doe"},
            {"name": "email", "value": "john@example.com"},
            {"name": "relationship", "value": "Other Adult"},
        ]
        result = handle_other_adult_contact_form(self.graph, self.invite_id, responses)
        self.assertIsInstance(result, list)

    def test_handle_consent_raises_with_missing_node_id(self):
        with self.assertRaises(KeyError):
            handle_consent(self.graph, self.invite_id, [{"name": "consent", "value": "true"}])

    def test_update_consent_and_advance_invalid_node(self):
        result = update_consent_and_advance(self.invite_id, "nonexistent", self.graph, "test")
        self.assertIn("Invalid node", result[0]["messages"][0])

    # def test_store_consent_form_data_populates_consent_fields(self):
    #     from consentbot.services import store_consent_form_data
    #     responses = [
    #         {"name": "consent_age_group", "value": ">=18"},
    #         {"name": "store_phi_other_studies", "value": "true"}
    #     ]
    #     consent = Consent.objects.filter(user=self.user).latest("created_at")
    #     store_consent_form_data(responses, consent)
    #     consent.refresh_from_db()
    #     self.assertTrue(consent.store_phi_other_studies)
