from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Organization
from cloud_accounts.models import CloudAccount, CostRecord
from datetime import date


class AnalyticsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Analytics Test Org")

        self.user = User.objects.create_user(
            username="analytics_test_user",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.ADMIN,
        )

        self.cloud_account = CloudAccount.objects.create(
            organization=self.org,
            name="Test Account",
            aws_access_key_id="fake",
            aws_secret_access_key="fake",
        )
        CostRecord.objects.create(
            cloud_account=self.cloud_account,
            service="Amazon EC2",
            amount=100.00,
            date=date.today(),
            is_synthetic=True,
        )
        CostRecord.objects.create(
            cloud_account=self.cloud_account,
            service="Amazon S3",
            amount=50.00,
            date=date.today(),
            is_synthetic=True,
        )

    def _get_token(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "analytics_test_user", "password": "TestPass123!"},
            format="json",
        )
        return response.data["access"]

    def test_summary_returns_correct_total(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/analytics/summary/?days=30")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_cost"], 150.00)

    def test_summary_top_services_correct(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/analytics/summary/?days=30")
        top = response.data["top_services"]
        self.assertEqual(top[0]["service"], "Amazon EC2")
        self.assertEqual(top[0]["amount"], 100.00)

    def test_report_returns_csv(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/reports/monthly/?days=30")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_unauthenticated_blocked(self):
        response = self.client.get("/api/v1/analytics/summary/?days=30")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
