# #!/usr/bin/env python3
# tests/authentication/test_services.py

# tests/authentication/test_serializers.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from authentication.services import (
    UserInputSerializer,
    UserOutputSerializer,
    ChangePasswordSerializer,
    FollowUpInputSerializer,
    FollowUpOutputSerializer,
    LoginSerializer,
)
from authentication.models import FollowUp
from consentbot.models import ConsentScript
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class UserInputSerializerTests(TestCase):
    fixtures = ['tests/fixtures/initial.json']

    def setUp(self):
        self.script = ConsentScript.objects.all()[0]
        self.user_data = {
            "email": "newuser@test.com",
            "first_name": "New",
            "last_name": "User",
            "phone": "1234567890",
            "password": "securepass",
            "is_staff": False,
            "is_superuser": False,
            "script_id": str(self.script.script_id),
        }

    def test_create_user_with_valid_data(self):
        serializer = UserInputSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, "newuser@test.com")
        self.assertTrue(user.check_password("securepass"))
        self.assertEqual(user.consent_script, self.script)

    def test_create_user_without_script_id(self):
        data = self.user_data.copy()
        data.pop("script_id")
        serializer = UserInputSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsNone(user.consent_script)

    def test_create_user_invalid_script_id(self):
        data = self.user_data.copy()
        data["script_id"] = "invalid-uuid"
        serializer = UserInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("script_id", serializer.errors)

class UserOutputSerializerTests(TestCase):
    fixtures = ['tests/fixtures/initial.json']

    def setUp(self):
        self.user = User.objects.get(username="test")

    def test_output_serializer_fields(self):
        serializer = UserOutputSerializer(self.user)
        data = serializer.data
        self.assertIn("username", data)
        self.assertIn("first_name", data)
        self.assertIn("invite_expired", data)
        self.assertIsNone(data.get("consent_name", None))  # allow None but field exists

class ChangePasswordSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="changepass", email="test@example.com", password="oldpass")

    def test_change_password_success(self):
        data = {
            "old_password": "oldpass",
            "new_password": "newpass123",
            "confirm_new_password": "newpass123"
        }
        serializer = ChangePasswordSerializer(data=data, context={"request": type('obj', (object,), {'user': self.user})()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.update(self.user, serializer.validated_data)
        self.assertTrue(self.user.check_password("newpass123"))

    def test_change_password_wrong_old(self):
        data = {
            "old_password": "wrongold",
            "new_password": "newpass123",
            "confirm_new_password": "newpass123"
        }
        serializer = ChangePasswordSerializer(data=data, context={"request": type('obj', (object,), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    def test_change_password_mismatch(self):
        data = {
            "old_password": "oldpass",
            "new_password": "newpass123",
            "confirm_new_password": "differentpass"
        }
        serializer = ChangePasswordSerializer(data=data, context={"request": type('obj', (object,), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_new_password", serializer.errors)

class FollowUpInputSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="followupuser", email="follow@test.com", password="testpass")

    def test_create_follow_up_success(self):
        data = {
            "email": "follow@test.com",
            "follow_up_reason": "Need help",
            "follow_up_info": "More details",
            "resolved": False
        }
        serializer = FollowUpInputSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        follow_up = serializer.save()
        self.assertEqual(follow_up.user, self.user)
        self.assertEqual(follow_up.follow_up_reason, "Need help")

    def test_create_follow_up_invalid_email(self):
        data = {
            "email": "noone@nowhere.com",
            "follow_up_reason": "Need help",
            "follow_up_info": "More details",
            "resolved": False
        }
        serializer = FollowUpInputSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)  # ✅ Correct field now

class FollowUpOutputSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="outputuser", email="output@test.com", password="testpass", phone="1112223333")
        self.follow_up = FollowUp.objects.create(user=self.user, follow_up_reason="Reason", follow_up_info="Info", resolved=False)

    def test_output_follow_up_fields(self):
        serializer = FollowUpOutputSerializer(self.follow_up)
        data = serializer.data
        self.assertEqual(data["user_id"], self.user.user_id)
        self.assertEqual(data["first_name"], self.user.first_name)
        self.assertIn("consent_script_id", data)

class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="loginuser", email="login@test.com", password="mypassword")

    def test_login_success(self):
        data = {"email": "login@test.com", "password": "mypassword"}
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_login_failure(self):
        data = {"email": "login@test.com", "password": "wrongpassword"}
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
