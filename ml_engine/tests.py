from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Organization
from cloud_accounts.models import CloudAccount, CostRecord
from datetime import date, timedelta


class MLForecastTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="ML Test Org")

        self.user = User.objects.create_user(
            username="ml_test_user",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.ADMIN,
        )

        self.cloud_account = CloudAccount.objects.create(
            organization=self.org,
            name="ML Test Account",
            aws_access_key_id="fake",
            aws_secret_access_key="fake",
        )

        # create 40 days of cost data - enough to train a model
        today = date.today()
        for i in range(40):
            CostRecord.objects.create(
                cloud_account=self.cloud_account,
                service="Amazon EC2",
                amount=50 + (i % 7) * 5,  # some variance
                date=today - timedelta(days=39 - i),
                is_synthetic=True,
            )

    def _get_token(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "ml_test_user", "password": "TestPass123!"},
            format="json",
        )
        return response.data["access"]

    def test_forecast_endpoint_returns_prediction(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/predictions/forecast/?days=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("predicted_total", response.data)
        self.assertIn("daily_predictions", response.data)
        self.assertEqual(len(response.data["daily_predictions"]), 10)

    def test_forecast_saved_to_history(self):
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.client.get("/api/v1/predictions/forecast/?days=10")
        response = self.client.get("/api/v1/predictions/history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_insufficient_data_returns_400(self):
        # new org with no cost data at all
        empty_org = Organization.objects.create(name="Empty Org")
        empty_user = User.objects.create_user(
            username="empty_org_user",
            password="TestPass123!",
            organization=empty_org,
            role=User.Role.ADMIN,
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "empty_org_user", "password": "TestPass123!"},
            format="json",
        )
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/predictions/forecast/?days=10")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
