from django.db import models
from users.models import Organization
import uuid


class ForecastResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="forecasts",
    )
    forecast_period = models.CharField(max_length=50)
    predicted_total = models.DecimalField(max_digits=12, decimal_places=2)
    mae = models.FloatField()
    based_on_days = models.IntegerField()
    daily_predictions = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Forecast for {self.organization.name} - {self.created_at.date()}"
