from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import services
from .models import Follow, Block


User = get_user_model()


class BasicUserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    has_blocked_me = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "followers_count",
            "following_count",
            "is_following",
            "is_blocked",
            "has_blocked_me",
        ]

    def get_followers_count(self, obj) -> int:
        return services.get_followers_count(obj)

    def get_following_count(self, obj) -> int:
        return services.get_following_count(obj)

    def get_is_following(self, obj) -> bool:
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return Follow.objects.filter(
            follower=request.user,
            following=obj,
        ).exists()

    def get_is_blocked(self, obj) -> bool:
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return Block.objects.filter(
            blocker=request.user,
            blocked=obj,
        ).exists()

    def get_has_blocked_me(self, obj) -> bool:
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return Block.objects.filter(
            blocker=obj,
            blocked=request.user,
        ).exists()


class FollowSerializer(serializers.ModelSerializer):
    follower = BasicUserSerializer(read_only=True)
    following = BasicUserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "following",
            "created_at",
        ]


class BlockSerializer(serializers.ModelSerializer):
    blocker = BasicUserSerializer(read_only=True)
    blocked = BasicUserSerializer(read_only=True)

    class Meta:
        model = Block
        fields = [
            "id",
            "blocker",
            "blocked",
            "created_at",
        ]


class SocialActionResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
