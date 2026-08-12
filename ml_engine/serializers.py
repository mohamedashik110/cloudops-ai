from rest_framework import serializers
from .models import ForecastResult


class ForecastResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastResult
        fields = [
            "id", "forecast_period", "predicted_total",
            "mae", "based_on_days", "daily_predictions", "created_at",
        ]
