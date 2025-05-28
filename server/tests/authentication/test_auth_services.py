#!/usr/bin/env python
# tests/authentication/test_auth_services.py

from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from authentication.models import FollowUp, Feedback
from authentication.services import (
    UserInputSerializer,
    UserOutputSerializer,
    FollowUpInputSerializer,
    FollowUpOutputSerializer,
    FeedbackInputSerializer,
    FeedbackOutputSerializer,
    ChangePasswordSerializer,
    create_follow_up_with_user
)

User = get_user_model()

class AuthServiceSerializerTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(username="test")
        self.user.set_password("testpass123")
        self.user.save()

    def test_user_input_serializer_create(self):
        payload = {
            "email": "new@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "1234567890",
            "password": "testpass123",
            "is_staff": False,
            "is_superuser": False,
        }
        serializer = UserInputSerializer(data=payload, context={"request": None})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, payload["email"])

    def test_user_output_serializer(self):
        serializer = UserOutputSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["username"], self.user.username)
        self.assertIn("first_test_score", data)
        self.assertIn("invite_expired", data)

    def test_followup_input_serializer_create(self):
        payload = {
            "email": self.user.email,
            "follow_up_reason": "Feedback",
            "follow_up_info": "More details here"
        }
        serializer = FollowUpInputSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        follow_up = serializer.save()
        self.assertEqual(follow_up.user, self.user)

    def test_followup_output_serializer(self):
        follow_up = FollowUp.objects.create(
            user=self.user,
            follow_up_reason="Test reason",
            follow_up_info="Test info"
        )
        serializer = FollowUpOutputSerializer(follow_up)
        data = serializer.data
        self.assertEqual(data["user_id"], self.user.user_id)
        self.assertEqual(data["email"], self.user.email)

    def test_feedback_serializers(self):
        input_data = {
            "user": self.user.pk,
            "satisfaction": "Satisfied",
            "suggestions": "None"
        }
        in_serializer = FeedbackInputSerializer(data=input_data)
        self.assertTrue(in_serializer.is_valid(), in_serializer.errors)
        feedback = in_serializer.save()
        out_serializer = FeedbackOutputSerializer(feedback)
        self.assertEqual(out_serializer.data["user_id"], str(self.user.pk))

    def test_anon_feedback_serializers(self):
        input_data = {
            "satisfaction": "Satisfied",
            "suggestions": "Very specific message for testing"
        }
        in_serializer = FeedbackInputSerializer(data=input_data)
        self.assertTrue(in_serializer.is_valid(), in_serializer.errors)
        feedback = in_serializer.save()
        out_serializer = FeedbackOutputSerializer(feedback)
        self.assertEqual(out_serializer.data["suggestions"], "Very specific message for testing")

    def test_change_password_serializer_valid(self):
        context = {"request": type("Request", (), {"user": self.user})()}
        payload = {
            "old_password": "testpass123",
            "new_password": "newpass456",
            "confirm_new_password": "newpass456"
        }
        serializer = ChangePasswordSerializer(data=payload, context=context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.update(self.user, serializer.validated_data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))

    def test_change_password_serializer_wrong_old_password(self):
        context = {"request": type("Request", (), {"user": self.user})()}
        payload = {
            "old_password": "wrongpassword",
            "new_password": "newpass456",
            "confirm_new_password": "newpass456"
        }
        serializer = ChangePasswordSerializer(data=payload, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    def test_change_password_serializer_mismatched_passwords(self):
        context = {"request": type("Request", (), {"user": self.user})()}
        payload = {
            "old_password": "testpass123",
            "new_password": "newpass456",
            "confirm_new_password": "wrongpass456"
        }
        serializer = ChangePasswordSerializer(data=payload, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_new_password", serializer.errors)

    def test_followup_input_serializer_invalid_email(self):
        payload = {
            "email": "nonexistent@example.com",
            "follow_up_reason": "Question",
            "follow_up_info": "Where's my sample?"
        }
        serializer = FollowUpInputSerializer(data=payload)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.save()
        self.assertIn("No user found with that email.", str(context.exception))

    def test_create_follow_up_with_user(self):
        invite_id = str(self.user.consent_urls.first().consent_url)
        reason = "Help"
        more_info = "Please follow up."
        follow_up = create_follow_up_with_user(invite_id, reason, more_info)
        self.assertEqual(follow_up.user, self.user)
        self.assertEqual(follow_up.follow_up_reason, reason)
        self.assertEqual(follow_up.follow_up_info, more_info)