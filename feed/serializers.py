from django.contrib.auth import get_user_model
from rest_framework import serializers

from posts.models import Hashtag
from posts.serializers import PostSerializer


User = get_user_model()


class FeedUserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "display_name",
            "avatar",
        ]

    def get_display_name(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and getattr(profile, "display_name", None):
            return profile.display_name
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_avatar(self, obj):
        request = self.context.get("request")
        profile = getattr(obj, "profile", None)

        if not profile or not getattr(profile, "avatar", None):
            return None

        avatar_url = profile.avatar.url
        if request:
            return request.build_absolute_uri(avatar_url)
        return avatar_url


class HashtagSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Hashtag
        fields = [
            "id",
            "name",
            "posts_count",
            "created_at",
        ]

    def get_posts_count(self, obj):
        return obj.hashtag_posts.filter(post__deleted_at__isnull=True).count()
