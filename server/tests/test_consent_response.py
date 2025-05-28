#!/usr/bin/env python
# tests/test_consent_response.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from consentbot.models import ConsentSession


class ConsentResponseTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.invite = ConsentSession.objects.first()

    def test_get_start_of_consent(self):
        url = reverse("consent-response-detail", args=[str(self.invite.session_slug)])
        response = self.client.get(url, {"node_id": "start"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chat", data)
        self.assertIn("next_node_id", data)
        self.assertTrue(len(data["chat"]) > 0)
