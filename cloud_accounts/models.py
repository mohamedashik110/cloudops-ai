from django.db import models
from users.models import Organization
import uuid
import secrets


class CloudAccount(models.Model):
    class Provider(models.TextChoices):
        AWS = "aws", "AWS"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONNECTED = "connected", "Connected"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="cloud_accounts",
    )
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.AWS)

    role_arn = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="ARN of the IAM Role the company created for CloudOps AI to assume.",
    )
    external_id = models.CharField(
        max_length=64,
        default=secrets.token_hex,
        help_text="Unique external ID required in the role's trust policy, prevents the confused deputy problem.",
    )

    aws_region = models.CharField(max_length=50, default="us-east-1")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class CostRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cloud_account = models.ForeignKey(
        CloudAccount,
        on_delete=models.CASCADE,
        related_name="cost_records",
    )
    service = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    currency = models.CharField(max_length=10, default="USD")
    date = models.DateField()
    region = models.CharField(max_length=50, blank=True, null=True)
    is_synthetic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["cloud_account", "date"]),
            models.Index(fields=["service"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.service} - {self.amount} {self.currency} ({self.date})"
