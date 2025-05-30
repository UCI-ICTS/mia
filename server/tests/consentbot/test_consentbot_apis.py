#!/usr/bin/env python
# tests/consentbot/test_consentbot_apis.py

import uuid
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from consentbot.models import ConsentSession, ConsentScript, Consent
from django.contrib.auth import get_user_model
import json

class ConsentSessionViewSetTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.invite = ConsentSession.objects.first()
        self.user = self.invite.user
        self.client.force_authenticate(user=self.user)

    def test_invite_url_detail_returns_user_info(self):
        url = f"/mia/consentbot/consent-url/{self.user.username}/invite-link/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_id"], str(self.user.pk))


class ConsentResponseViewSetTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.invite = ConsentSession.objects.first()

    def test_valid_get(self):
        url = f"/mia/consentbot/consent-response/{self.invite.session_slug}/?node_id=start"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("chat", response.data)
        self.assertIn("node_id", response.data['chat'][-1])

    def test_missing_node_param(self):
        url = f"/mia/consentbot/consent-response/{self.invite.session_slug}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("node_id", response.data['error'])

    def test_invalid_session_slug(self):
        bad_uuid = uuid.uuid4()
        url = f"/mia/consentbot/consent-response/{bad_uuid}/?node_id=start"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data['error'])

    def test_button_post(self):
        url = f"/mia/consentbot/consent-response/"
        response = self.client.post(url, {
            "session_slug": str(self.invite.session_slug),
            "node_id": "AimWGCA",
            "form_type": "consent",
            "form_responses": [
                {"name": "node_id", "value": "AimWGCA"},
                {"name": "consent", "value": "true"},
                {"name": "fullname", "value": "Jane Example"}
            ]
        }, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("chat", response.data)
        self.assertIn("node_id", response.data['chat'][-1])

    def test_invalid_post_payload(self):
        url = f"/mia/consentbot/consent-response/"
        response = self.client.post(url, {"node_id": 1234}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("session_slug", response.data['error'])

    def test_unknown_form_type(self):
        url = f"/mia/consentbot/consent-response/"
        response = self.client.post(url, {
            "session_slug": str(self.invite.session_slug),
            "node_id": "start",
            "form_type": "not_real",
            "form_responses": []
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

class ConsentViewSetTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.invite = ConsentSession.objects.first()
        self.user = self.invite.user
        self.user.consent_script = ConsentScript.objects.first()
        self.user.save()

    def test_consent_list(self):
        url = "/mia/consentbot/consent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))

    def test_consent_retrieve(self):
        url = f"/mia/consentbot/consent/{self.invite.session_slug}/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 201])
        self.assertIn("chat", response.data)
        self.assertEqual(response.data['consent']["user_id"], str(self.user.pk))

    # def test_consent_create(self):
    #     payload = {
    #         "user_id": str(self.user.pk),
    #         "consent_age_group": ">=18",
    #         "store_sample_this_study": True,
    #         "store_sample_other_studies": False,
    #         "store_phi_this_study": True,
    #         "store_phi_other_studies": False,
    #         "return_primary_results": False,
    #         "return_actionable_secondary_results": False,
    #         "return_secondary_results": False,
    #         "consent_statements": "Agree",
    #         "user_full_name_consent": "Test User"
    #     }
    #     url = "/mia/consentbot/consent/"
    #     response = self.client.post(url, data=payload, format="json")
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.data["user_id"], str(self.user.pk))

    # def test_consent_update(self):
    #     import pdb; pdb.set_trace()
    #     instance = self.user.consents.latest("created_at")
    #     url = f"/mia/consentbot/consent/{instance.pk}/"
    #     response = self.client.put(url, data={"consent_age_group": "7-17"}, format="json")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data["consent_age_group"], "7-17")

    # def test_consent_destroy(self):
    #     import pdb; pdb.set_trace()
    #     instance = self.user.consents.latest("created_at")
    #     url = f"/mia/consentbot/consent/{instance.pk}/"
    #     response = self.client.delete(url)
    #     self.assertEqual(response.status_code, 204)