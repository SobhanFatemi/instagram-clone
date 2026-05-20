from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "username",
            "display_name",
            "bio",
            "avatar",
            "is_private",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "username",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_display_name(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Display name must be at least 2 characters long."
            )
        return value.strip() if value else value

    def validate_bio(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError(
                "Bio cannot be longer than 1000 characters."
            )
        return value
