from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Organization
from cloud_accounts.models import CloudAccount, CostRecord
from datetime import date


class CloudAccountsRBACTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org 2")

        self.admin_user = User.objects.create_user(
            username="ca_admin_test",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.viewer_user = User.objects.create_user(
            username="ca_viewer_test",
            password="TestPass123!",
            organization=self.org,
            role=User.Role.VIEWER,
        )

        self.cloud_account = CloudAccount.objects.create(
            organization=self.org,
            name="Test Cloud Account",
            aws_access_key_id="fake",
            aws_secret_access_key="fake",
        )
        CostRecord.objects.create(
            cloud_account=self.cloud_account,
            service="Amazon EC2",
            amount=10.50,
            date=date.today(),
            is_synthetic=True,
        )

    def _get_token(self, username, password):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        return response.data["access"]

    def test_viewer_can_read_cost_records(self):
        token = self._get_token("ca_viewer_test", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/cost-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_create_cloud_account(self):
        token = self._get_token("ca_viewer_test", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/cloud-accounts/", {
            "name": "Blocked Account",
            "aws_access_key_id": "fake",
            "aws_secret_access_key": "fake",
            "aws_region": "us-east-1",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_cloud_account(self):
        token = self._get_token("ca_admin_test", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/api/v1/cloud-accounts/", {
            "name": "Allowed Account",
            "aws_access_key_id": "fake",
            "aws_secret_access_key": "fake",
            "aws_region": "us-east-1",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_org_isolation_on_cost_records(self):
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(
            username="other_org_user",
            password="TestPass123!",
            organization=other_org,
            role=User.Role.ADMIN,
        )
        token = self._get_token("other_org_user", "TestPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/v1/cost-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # should see NO records from Test Org 2
