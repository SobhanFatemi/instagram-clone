from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Story, StoryComment, StoryView


class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["id", "media_type", "file", "text"]

    def validate(self, attrs):
        media_type = attrs.get("media_type")
        file = attrs.get("file")

        if not file:
            raise serializers.ValidationError({"file": "This field is required."})

        if media_type not in ["image", "video"]:
            raise serializers.ValidationError(
                {"media_type": "media_type must be either 'image' or 'video'."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Story.objects.create(
            user=request.user,
            media_type=validated_data["media_type"],
            file=validated_data["file"],
            text=validated_data.get("text", ""),
            expires_at=timezone.now() + timedelta(hours=24),
        )


class StoryListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    is_viewed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "username",
            "media_type",
            "file",
            "text",
            "created_at",
            "expires_at",
            "views_count",
            "is_viewed",
        ]


class StoryDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    is_viewed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "username",
            "media_type",
            "file",
            "text",
            "created_at",
            "expires_at",
            "views_count",
            "is_viewed",
        ]


class StoryViewerSerializer(serializers.ModelSerializer):
    viewer_id = serializers.IntegerField(source="viewer.id", read_only=True)
    username = serializers.CharField(source="viewer.username", read_only=True)

    class Meta:
        model = StoryView
        fields = ["viewer_id", "username", "created_at"]


class StoryGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    latest_story_created_at = serializers.DateTimeField()
    stories = StoryListSerializer(many=True)


class StoryCommentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = StoryComment
        fields = [
            "id",
            "story",
            "user_id",
            "username",
            "parent",
            "content",
            "created_at",
            "replies",
        ]
        read_only_fields = ["id", "user_id", "username", "created_at", "replies"]

    def get_replies(self, obj):
        replies = obj.replies.filter(deleted_at__isnull=True).select_related("user")
        return StoryCommentSerializer(replies, many=True, context=self.context).data


class StoryCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryComment
        fields = ["id", "story", "parent", "content"]
        read_only_fields = ["id"]

    def validate_story(self, value):
        if value.deleted_at is not None:
            raise serializers.ValidationError("Story not found.")
        if value.expires_at <= timezone.now():
            raise serializers.ValidationError("Cannot comment on expired story.")
        return value

    def validate_parent(self, value):
        if value is None:
            return value

        if value.deleted_at is not None:
            raise serializers.ValidationError("Parent comment not found.")

        if value.parent_id is not None:
            raise serializers.ValidationError("You can only reply to a top-level comment.")

        return value

    def validate(self, attrs):
        story = attrs.get("story")
        parent = attrs.get("parent")

        if parent and parent.story_id != story.id:
            raise serializers.ValidationError(
                {"parent": "Parent comment must belong to the same story."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return StoryComment.objects.create(
            story=validated_data["story"],
            user=request.user,
            parent=validated_data.get("parent"),
            content=validated_data["content"],
        )
