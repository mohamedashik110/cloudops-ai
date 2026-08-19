from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Organization
from cloud_accounts.models import CloudAccount, CostRecord
from datetime import date


class CopilotTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Copilot Test Org")

        self.user = User.objects.create_user(
            username="copilot_test_user",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.ADMIN,
        )

        self.cloud_account = CloudAccount.objects.create(
            organization=self.org,
            name="Copilot Test Account",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        CostRecord.objects.create(
            cloud_account=self.cloud_account,
            service="Amazon EC2",
            amount=100.00,
            date=date.today(),
            is_synthetic=True,
        )

    def _get_token(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "copilot_test_user", "password": "TestPass123!"},
            format="json",
        )
        return response.data["access"]

    def test_chat_requires_question(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/copilot/chat/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_returns_grounded_answer(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(
            "/api/v1/copilot/chat/",
            {"question": "What is our total cost?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("answer", response.data)
        self.assertIn("sources", response.data)
        self.assertEqual(response.data["sources"]["total_cost"], 100.00)

    def test_chat_unauthenticated_blocked(self):
        response = self.client.post(
            "/api/v1/copilot/chat/",
            {"question": "What is our total cost?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
