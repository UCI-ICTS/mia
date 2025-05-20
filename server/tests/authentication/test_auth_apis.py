#!/usr/bin/env python
# tests/authentication/test_auth_apis.py

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import User


class AuthApiTests(TestCase):
    fixtures = ["tests/fixtures/test_data.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(username="test")
        self.password = "example-password"
        self.user.set_password(self.password)
        self.user.save()

    def test_login_valid_credentials(self):
        response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": self.password
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": "wrong-password"
        }, format="json")
        self.assertEqual(response.status_code, 401)

    def test_token_refresh(self):
        login_response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": self.password
        }, format="json")
        refresh_token = login_response.data["refresh"]
        response = self.client.post("/mia/auth/refresh/", {
            "refresh": refresh_token
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_token_verify(self):
        login_response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": self.password
        }, format="json")
        access_token = login_response.data["access"]
        response = self.client.post("/mia/auth/verify/", {
            "token": access_token
        }, format="json")
        self.assertEqual(response.status_code, 200)

    def test_logout_blacklists_refresh_token(self):
        login_response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": self.password
        }, format="json")
        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post("/mia/auth/logout/", {
            "refresh": refresh_token
        }, format="json")
        self.assertEqual(response.status_code, 200)

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/mia/auth/change_password/", {
            "old_password": self.password,
            "new_password": "newsecurepassword123",
            "confirm_new_password": "newsecurepassword123"
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Password changed successfully")

    def test_change_password_fail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/mia/auth/change_password/", {
            "old_password": "bad password",
            "new_password": "newsecurepassword123",
            "confirm_new_password": "newsecurepassword123"
        }, format="json")
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["old_password"][0], "Incorrect password")

    def test_get_csrf_token(self):
        response = self.client.get("/mia/auth/csrf/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.text)
        self.assertIn("CSRF cookie set", response.text)

    def test_user_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/mia/auth/users/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 1)

    def test_user_create(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "strongpass",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post("/mia/auth/users/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], payload["email"])

    def test_user_re_create(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "email": "jdoe@testing.com",
            "username": "newuser",
            "password": "strongpass",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post("/mia/auth/users/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["email"][0], "user with this email already exists.")

    def test_user_update(self):
        self.client.force_authenticate(user=self.user)
        payload = {"first_name": "Updated", "last_name": "Name"}
        response = self.client.put(f"/mia/auth/users/{self.user.username}/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_user_update_dne(self):
        self.client.force_authenticate(user=self.user)
        payload = {"first_name": "Updated", "last_name": "Name"}
        response = self.client.put(f"/mia/auth/users/DNE/", payload, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "User not found")

    def test_user_delete(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/mia/auth/users/{self.user.username}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(username=self.user.username).exists())

    def test_user_delete_dne(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/mia/auth/users/dne/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "User not found")

    def test_followup_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/mia/auth/follow-ups/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_followup_create(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "email": "test@test.com",
            "message": "This is a test message",
            "full_name": "Test User"
        }
        response = self.client.post("/mia/auth/follow-ups/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], payload["email"])
