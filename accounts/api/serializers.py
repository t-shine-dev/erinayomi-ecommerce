from rest_framework import serializers

from ..models import SavedAddress, User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "created_at",
        )
        read_only_fields = ("username", "created_at")


class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = (
            "id",
            "label",
            "full_name",
            "phone_number",
            "address_line",
            "city",
            "state",
            "is_default",
            "created_at",
        )
        read_only_fields = ("id", "created_at")