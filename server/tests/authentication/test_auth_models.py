#!/usr/bin/env python
# tests/authentication/test_auth_apis.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from authentication.models import Feedback, FollowUp

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="testuser@example.com",
            password="securepass123",
            first_name="Test",
            last_name="User"
        )
        self.assertEqual(user.email, "testuser@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("securepass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_str(self):
        user = User.objects.create_user(
            email="strtest@example.com",
            password="pass",
            first_name="Str",
            last_name="Test"
        )
        self.assertEqual(str(user), "Str Test")


class FollowUpModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="followup@example.com",
            password="pass",
            first_name="Follow",
            last_name="Up"
        )

    def test_followup_creation(self):
        followup = FollowUp.objects.create(
            user=self.user,
            follow_up_reason="Need help",
            follow_up_info="More details..."
        )
        self.assertEqual(followup.user, self.user)
        self.assertEqual(followup.follow_up_reason, "Need help")
        self.assertFalse(followup.resolved)
        self.assertIsNotNone(followup.created_at)


class FeedbackModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="feedback@example.com",
            password="pass",
            first_name="Feed",
            last_name="Back"
        )

    def test_feedback_creation(self):
        feedback = Feedback.objects.create(
            user=self.user,
            satisfaction="Satisfied",
            suggestions="None"
        )
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.satisfaction, "Satisfied")
        self.assertEqual(feedback.suggestions, "None")
        self.assertIsNotNone(feedback.created_at)
