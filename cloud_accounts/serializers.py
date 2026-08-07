from rest_framework import serializers
from .models import CloudAccount, CostRecord


class CloudAccountSerializer(serializers.ModelSerializer):
    aws_secret_access_key = serializers.CharField(write_only=True)
    aws_access_key_id = serializers.CharField(write_only=True)

    class Meta:
        model = CloudAccount
        fields = [
            "id", "name", "provider", "aws_access_key_id",
            "aws_secret_access_key", "aws_region", "status",
            "last_synced_at", "created_at",
        ]
        read_only_fields = ["id", "status", "last_synced_at", "created_at"]

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        return super().create(validated_data)


class CostRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostRecord
        fields = [
            "id", "service", "amount", "currency", "date",
            "region", "is_synthetic", "cloud_account",
        ]
