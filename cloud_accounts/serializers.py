from rest_framework import serializers
from .models import CloudAccount, CostRecord


class CloudAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudAccount
        fields = [
            "id", "name", "provider", "role_arn", "external_id",
            "aws_region", "status", "last_synced_at", "created_at",
        ]
        read_only_fields = ["id", "external_id", "status", "last_synced_at", "created_at"]

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
