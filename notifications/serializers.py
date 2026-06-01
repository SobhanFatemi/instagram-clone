from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Notification


class NotificationActorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_display_name(self, obj) -> str:
        profile = getattr(obj, "profile", None)
        if profile and hasattr(profile, "display_name"):
            return profile.display_name
        return obj.username

    def get_avatar(self, obj) -> str | None:
        request = self.context.get("request")
        profile = getattr(obj, "profile", None)

        if not profile or not hasattr(profile, "avatar") or not profile.avatar:
            return None

        try:
            url = profile.avatar.url
        except Exception:
            return None

        if request:
            return request.build_absolute_uri(url)

        return url


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "actor",
            "notification_type",
            "message",
            "target",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "actor",
            "notification_type",
            "message",
            "target",
            "is_read",
            "created_at",
        ]

    @extend_schema_field(NotificationActorSerializer)
    def get_actor(self, obj):
        if not obj.actor:
            return None

        return NotificationActorSerializer(
            obj.actor,
            context=self.context,
        ).data

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_target(self, obj):
        if not obj.target_content_type or not obj.target_object_id:
            return None

        target = obj.target

        data = {
            "app": obj.target_content_type.app_label,
            "model": obj.target_content_type.model,
            "id": obj.target_object_id,
        }

        if target is None:
            return data

        if hasattr(target, "post_id"):
            data["post_id"] = target.post_id

        if hasattr(target, "user_id"):
            data["user_id"] = target.user_id

        if hasattr(target, "caption"):
            data["caption"] = target.caption

        if hasattr(target, "text"):
            data["text"] = target.text

        return data


class UnreadCountResponseSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()


class MarkReadResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class MarkAllReadResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    updated = serializers.IntegerField()


class ClearNotificationsResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    deleted = serializers.IntegerField()
