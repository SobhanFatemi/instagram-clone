from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from common.models import SoftDeleteModel, TimeStampedModel


class Post(SoftDeleteModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    caption = models.TextField(blank=True)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["author", "created_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["deleted_at"]),
            models.Index(fields=["like_count"]),
            models.Index(fields=["view_count"]),
        ]

    def __str__(self):
        return f"Post<{self.id}> by {self.author_id}"


class PostMedia(TimeStampedModel):
    TYPE_IMAGE = "image"
    TYPE_VIDEO = "video"

    TYPE_CHOICES = [
        (TYPE_IMAGE, "Image"),
        (TYPE_VIDEO, "Video"),
    ]

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="media_items",
    )
    media_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    media = models.FileField(upload_to="posts/")
    sort_order = models.PositiveIntegerField(default=0)
    thumbnail = models.ImageField(upload_to="posts/thumbnails/", null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "sort_order"],
                name="unique_post_media_sort_order",
            ),
        ]
        indexes = [
            models.Index(fields=["post", "sort_order"]),
            models.Index(fields=["media_type"]),
        ]

    def __str__(self):
        return f"PostMedia<{self.post_id}:{self.sort_order}>"


class Hashtag(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_hashtags",
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name="hashtag_posts",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "hashtag"],
                name="unique_post_hashtag",
            ),
        ]
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["hashtag"]),
        ]

    def __str__(self):
        return f"{self.post_id} - {self.hashtag_id}"


class PostLike(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_post_like",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "post"]),
            models.Index(fields=["post", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} likes {self.post_id}"


class SavedPost(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_posts",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="saved_by",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_saved_post",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["post"]),
        ]

    def __str__(self):
        return f"{self.user_id} saved {self.post_id}"


class Comment(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"Comment<{self.id}>"
