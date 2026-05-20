from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from common.models import SoftDeleteModel


class Notification(SoftDeleteModel):
    class NotificationType(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        MENTION = "mention", "Mention"
        SYSTEM = "system", "System"
        MESSAGE = "message", "Message"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )

    message = models.CharField(max_length=255, blank=True)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("target_content_type", "target_object_id")

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.notification_type}"
