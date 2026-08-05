from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Organization


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    organization_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "organization_name"]

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name")
        organization, _ = Organization.objects.get_or_create(name=org_name)

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            organization=organization,
            role=User.Role.ADMIN,  # first user of an org becomes Admin
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "organization", "organization_name"]
        read_only_fields = ["role", "organization"]