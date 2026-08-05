from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Organization


class RBACTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")

        self.admin_user = User.objects.create_user(
            username="admin_test",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.viewer_user = User.objects.create_user(
            username="viewer_test",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.VIEWER,
        )

    def _get_token(self, username, password):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        return response.data["access"]

    def test_admin_can_access_org_users(self):
        token = self._get_token("admin_test", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/auth/org-users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_access_org_users(self):
        token = self._get_token("viewer_test", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/auth/org-users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/v1/auth/org-users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)