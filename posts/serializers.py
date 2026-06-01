from pathlib import Path

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Comment, Hashtag, Post, PostHashtag, PostMedia, SavedPost


class PostMediaSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "media_type",
            "media",
            "sort_order",
            "thumbnail",
            "duration_seconds",
            "created_at",
            "updated_at",
        ]

    def get_media(self, obj) -> str | None:
        request = self.context.get("request")
        if not obj.media:
            return None
        url = obj.media.url
        return request.build_absolute_uri(url) if request else url

    def get_thumbnail(self, obj) -> str | None:
        request = self.context.get("request")
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        return request.build_absolute_uri(url) if request else url


class PostSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    media_items = PostMediaSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField() 

    class Meta:
        model = Post
        fields = [
            "id",
            "author_id",
            "author_username",
            "author_display_name",
            "author_avatar",
            "caption",
            "like_count",
            "comment_count",
            "save_count",
            "view_count",
            "media_items",
            "hashtags",
            "is_liked",
            "is_saved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_author_display_name(self, obj) -> str:
        profile = getattr(obj.author, "profile", None)
        if profile and profile.display_name:
            return profile.display_name

        user = obj.author
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name if full_name else user.username

    def get_author_avatar(self, obj) -> str | None:
        request = self.context.get("request")
        profile = getattr(obj.author, "profile", None)

        if not profile or not profile.avatar:
            return None

        url = profile.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_liked(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_saved(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saved_by.filter(user=request.user).exists()
    
    def get_hashtags(self, obj) -> list[str]:
        return list(
            obj.post_hashtags
            .select_related("hashtag")
            .values_list("hashtag__name", flat=True)
        )



class PostCreateUpdateSerializer(serializers.ModelSerializer):
    media = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True,
        allow_empty=False,
        error_messages={
            "required": "At least one media item is required.",
            "empty": "At least one media item is required.",
        },
    )

    hashtags = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            "caption",
            "media",
            "hashtags",
        ]

    def validate_caption(self, value):
        value = value.strip()
        if len(value) > 2200:
            raise serializers.ValidationError(
                "Caption cannot be longer than 2200 characters."
            )
        return value

    def validate_media(self, media):
        if not media:
            raise serializers.ValidationError("At least one media item is required.")

        if len(media) > 10:
            raise serializers.ValidationError("You can upload at most 10 media items.")

        allowed_image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        allowed_video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        max_image_size = 10 * 1024 * 1024
        max_video_size = 100 * 1024 * 1024

        for item in media:
            ext = Path(item.name).suffix.lower()

            if ext in allowed_image_exts:
                if item.size > max_image_size:
                    raise serializers.ValidationError(
                        f"Image '{item.name}' exceeds 10MB."
                    )
            elif ext in allowed_video_exts:
                if item.size > max_video_size:
                    raise serializers.ValidationError(
                        f"Video '{item.name}' exceeds 100MB."
                    )
            else:
                raise serializers.ValidationError(
                    f"Unsupported media type '{item.name}'."
                )

        return media

    def _detect_media_type(self, item):
        ext = Path(item.name).suffix.lower()
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

        if ext in image_exts:
            return PostMedia.TYPE_IMAGE
        if ext in video_exts:
            return PostMedia.TYPE_VIDEO

        raise serializers.ValidationError(
            f"Unsupported media type for '{item.name}'."
        )

    def _set_hashtags(self, post, hashtag_list):
        post.post_hashtags.all().delete()

        for tag in hashtag_list:
            name = tag.strip().lstrip("#").lower()
            if not name:
                continue

            hashtag, _ = Hashtag.objects.get_or_create(name=name)
            PostHashtag.objects.get_or_create(post=post, hashtag=hashtag)

    # FIXED: these methods are now inside the class
    def create(self, validated_data):
        media = validated_data.pop("media", None)
        hashtags = validated_data.pop("hashtags", [])

        if not media:
            raise serializers.ValidationError({
                "media": ["At least one media item is required."]
            })

        post = Post.objects.create(**validated_data)

        for index, item in enumerate(media):
            PostMedia.objects.create(
                post=post,
                media=item,
                media_type=self._detect_media_type(item),
                sort_order=index,
            )

        self._set_hashtags(post, hashtags)

        return post

    def update(self, instance, validated_data):
        media = validated_data.pop("media", None)
        hashtags = validated_data.pop("hashtags", None)

        instance.caption = validated_data.get("caption", instance.caption)
        instance.save(update_fields=["caption", "updated_at"])

        if media is not None:
            if not media:
                raise serializers.ValidationError({
                    "media": ["At least one media item is required."]
                })

            instance.media_items.all().delete()

            for index, item in enumerate(media):
                PostMedia.objects.create(
                    post=instance,
                    media=item,
                    media_type=self._detect_media_type(item),
                    sort_order=index,
                )

        if not instance.media_items.exists():
            raise serializers.ValidationError({
                "media": ["At least one media item is required."]
            })

        if hashtags is not None:
            self._set_hashtags(instance, hashtags)

        return instance


class SavedPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = SavedPost
        fields = ["id", "post", "created_at"]
        read_only_fields = fields


class CommentAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk", read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_display_name(self, obj) -> str:
        profile = getattr(obj, "profile", None)
        return profile.display_name if profile else ""

    def get_avatar(self, obj) -> str | None:
        request = self.context.get("request")
        profile = getattr(obj, "profile", None)

        if not profile or not profile.avatar:
            return None

        url = profile.avatar.url
        return request.build_absolute_uri(url) if request else url


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source="parent.id", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "parent_id",
            "author",
            "content",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(CommentAuthorSerializer)
    def get_author(self, obj):
        return CommentAuthorSerializer(
            obj.user,
            context=self.context,
        ).data

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []

        replies = (
            obj.replies
            .filter(deleted_at__isnull=True)
            .select_related("user", "user__profile")
            .order_by("created_at")
        )

        return CommentSerializer(
            replies,
            many=True,
            context=self.context,
        ).data


class CommentCreateSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.filter(deleted_at__isnull=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Comment cannot be longer than 2000 characters."
            )
        return value

    def validate_parent(self, value):
        post = self.context.get("post")

        if value and value.post_id != post.id:
            raise serializers.ValidationError(
                "Parent comment must belong to the same post."
            )

        if value and value.parent_id is not None:
            raise serializers.ValidationError(
                "You can only reply to a top-level comment."
            )

        return value


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content"]

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Comment cannot be longer than 2000 characters."
            )
        return value
