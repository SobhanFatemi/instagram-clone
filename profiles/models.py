from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Profile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
    )
    is_private = models.BooleanField(
        default=False,
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["display_name"]),
            models.Index(fields=["is_private"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        username = getattr(self.user, "username", None)
        return f"Profile<{username or self.user_id}>"
