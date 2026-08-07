from django.db import models
from users.models import Organization
import uuid


class CloudAccount(models.Model):
    class Provider(models.TextChoices):
        AWS = "aws", "AWS"
        # future: GCP, Azure

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

    # AWS credentials — stored here for now; will discuss secrets handling separately
    aws_access_key_id = models.CharField(max_length=255)
    aws_secret_access_key = models.CharField(max_length=255)
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
    service = models.CharField(max_length=255)  # e.g., "Amazon EC2", "Amazon S3"
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    currency = models.CharField(max_length=10, default="USD")
    date = models.DateField()
    region = models.CharField(max_length=50, blank=True, null=True)
    is_synthetic = models.BooleanField(default=False)  # flags demo data vs real AWS data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["cloud_account", "date"]),
            models.Index(fields=["service"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.service} - {self.amount} {self.currency} ({self.date})"