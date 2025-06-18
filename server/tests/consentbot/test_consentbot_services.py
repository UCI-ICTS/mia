#!/usr/bin/env python
# tests/consentbot/test_consentbot_services.py

from django.test import TestCase
from consentbot.models import Consent, ConsentSession
from consentbot.services import (
    handle_consent,
    handle_family_enrollment_form,
    handle_user_feedback_form,
    handle_other_adult_contact_form,
    update_consent_and_advance
)
from utils.cache import set_user_consent_history
from consentbot.selectors import get_script_from_session_slug
from django.contrib.auth import get_user_model

User = get_user_model()

class ConsentServiceTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.user = User.objects.get(username='test')
        self.invite = ConsentSession.objects.get(user=self.user)
        self.script = self.user.consent_script
        self.graph = self.script.script
        self.session_slug = str(self.invite.session_slug)

    def test_handle_consent_sets_flags_and_returns_chat(self):
        responses = [
            {"name": "node_id", "value": "start"},
            {"name": "consent", "value": "true"},
            {"name": "fullname", "value": "Jane Tester"}
        ]
        result = handle_consent(self.graph, self.session_slug, responses)
        import pdb; pdb.set_trace()
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
        set_user_consent_history(self.session_slug, history)
        responses = [{"value": ["myself", "myChildChildren"]}]
        result = handle_family_enrollment_form(self.graph, self.session_slug, responses)
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
        result = handle_user_feedback_form(self.graph, self.session_slug, responses)
        self.assertIsInstance(result, list)

    def test_handle_other_adult_contact_form_progresses_chat(self):
        responses = [
            {"name": "node_id", "value": "start"},
            {"name": "full_name", "value": "John Doe"},
            {"name": "email", "value": "john@example.com"},
            {"name": "relationship", "value": "Other Adult"},
        ]
        result = handle_other_adult_contact_form(self.graph, self.session_slug, responses)
        self.assertIsInstance(result, list)

    def test_handle_consent_raises_with_missing_node_id(self):
        response = handle_consent(self.graph, self.session_slug, [{"name": "consent", "value": "true"}])
        self.assertIsInstance(response, list)
        self.assertIn("Invalid node", response[0]["messages"][0])


    def test_update_consent_and_advance_invalid_node(self):
        result = update_consent_and_advance(self.session_slug, "nonexistent", self.graph, "test")
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
