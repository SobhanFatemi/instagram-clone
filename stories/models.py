from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class Story(SoftDeleteModel):
    TYPE_IMAGE = "image"
    TYPE_VIDEO = "video"

    TYPE_CHOICES = [
        (TYPE_IMAGE, "Image"),
        (TYPE_VIDEO, "Video"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories",
    )
    media_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    file = models.FileField(upload_to="stories/")
    text = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"Story<{self.id}> by {self.user_id}"


class StoryView(TimeStampedModel):
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="views",
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_views",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["story", "viewer"], name="unique_story_view"),
        ]
        indexes = [
            models.Index(fields=["story", "created_at"]),
            models.Index(fields=["viewer", "created_at"]),
        ]

    def __str__(self):
        return f"{self.viewer_id} viewed {self.story_id}"


class StoryComment(SoftDeleteModel):
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["story", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["deleted_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"StoryComment<{self.id}> story={self.story_id} user={self.user_id}"
