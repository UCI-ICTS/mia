# #!/usr/bin/env python3
# tests/authentication/test_auth_apis.py

import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from authentication.models import FollowUp
User = get_user_model()

class CSRFTokenTest(TestCase):
    def test_csrf_token_set(self):
        response = self.client.get(reverse('authentication:get_csrf_token'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('CSRF cookie set', response.content.decode())
        self.assertIn('csrftoken', response.cookies)


class JWTAuthTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.login_url = reverse('authentication:token_obtain_pair')
        self.refresh_url = reverse('authentication:token_refresh')
        self.verify_url = reverse('authentication:token_verify')
        self.logout_url = reverse('authentication:token_blacklist')

    def test_login_success(self):
        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertIn('user', response.json())

    def test_login_fail(self):
        response = self.client.post(self.login_url, {'email': 'wrong@example.com', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.refresh_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())

    def test_verify_token(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        response = self.client.post(self.verify_url, {'token': access_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_blacklist(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.logout_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="refreshuser", email="test@example.com", password="password123")
        self.refresh = str(RefreshToken.for_user(self.user))
        self.refresh_url = reverse('authentication:token_refresh')

    def test_refresh_success(self):
        response = self.client.post(self.refresh_url, {"refresh": self.refresh})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_refresh_invalid_token(self):
        response = self.client.post(self.refresh_url, {"refresh": "invalidtoken"})
        self.assertEqual(response.status_code, 401)


class TokenVerifyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="verifyuser", email="test@example.com", password="password123")
        self.access = str(AccessToken.for_user(self.user))
        self.verify_url = reverse('authentication:token_verify')

    def test_verify_success(self):
        response = self.client.post(self.verify_url, {"token": self.access})
        self.assertEqual(response.status_code, 200)

    def test_verify_invalid_token(self):
        response = self.client.post(self.verify_url, {"token": "invalidtoken"})
        self.assertEqual(response.status_code, 401)


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.login_url = reverse('authentication:token_obtain_pair')

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "email": "test@example.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertIn("user", response.json())

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("No active account", response.json()["detail"])


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="logoutuser", email="test@example.com", password="password123")
        self.refresh = str(RefreshToken.for_user(self.user))
        self.logout_url = reverse('authentication:token_blacklist')

    def test_logout_success(self):
        response = self.client.post(self.logout_url, {"refresh": self.refresh})
        self.assertEqual(response.status_code, 200)

    def test_logout_invalid_token(self):
        response = self.client.post(self.logout_url, {"refresh": "invalidtoken"})
        self.assertEqual(response.status_code, 401)


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="changepass", email="test@example.com", password="oldpass123")
        self.access = str(AccessToken.for_user(self.user))
        self.change_password_url = reverse('authentication:change_password')

    def test_change_password_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        response = self.client.post(self.change_password_url, {
            "old_password": "oldpass123",
            "new_password": "newpass456",
            "confirm_new_password": "newpass456"
        })
        # import pdb; pdb.set_trace()
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))

    def test_change_password_invalid_old(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        response = self.client.post(self.change_password_url, {
            "old_password": "wrongold",
            "new_password": "newpass456"
        })
        self.assertEqual(response.status_code, 400)


class FollowUpAPITest(TestCase):
    fixtures = ['tests/fixtures/initial.json']

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(username="test")
        self.follow_up = FollowUp.objects.first()
        self.access_token = str(AccessToken.for_user(self.user))
        self.list_url = reverse('authentication:follow_up-list')
        self.detail_url = lambda pk: reverse('authentication:follow_up-detail', kwargs={'pk': pk})


        # Create a follow-up entry
        self.follow_up = FollowUp.objects.create(
            user=self.user,
            follow_up_reason="Need help",
            follow_up_info="Test follow-up",
            resolved=False,
        )

    def test_list_follow_ups_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_list_follow_ups_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_follow_up_unauthenticated_allowed(self):
        payload = {
            "email": "test@test.com",
            "follow_up_reason": "Test Reason",
            "follow_up_info": "Test Info",
            "resolved": False
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['follow_up_reason'], "Test Reason")

    def test_create_follow_up_invalid_email(self):
        payload = {
            "email": "nonexistent@example.com",
            "follow_up_reason": "Test",
            "follow_up_info": "Info",
            "resolved": False
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_follow_up_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        payload = {"resolved": True}
        response = self.client.patch(self.detail_url(self.follow_up.pk), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.follow_up.refresh_from_db()
        self.assertTrue(self.follow_up.resolved)

    def test_partial_update_follow_up_unauthenticated(self):
        payload = {"resolved": True}
        response = self.client.patch(self.detail_url(self.follow_up.pk), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_invalid_follow_up(self):
        valid_but_nonexistent_uuid = uuid.uuid4()
        invalid_url = reverse('authentication:follow_up-detail', kwargs={'pk': valid_but_nonexistent_uuid})
        response = self.client.patch(invalid_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
