from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from common.models import SoftDeleteModel, TimeStampedModel


def message_attachment_upload_to(instance, filename):
    return f"messaging/conversations/{instance.conversation_id}/messages/{filename}"


class Conversation(TimeStampedModel):
    TYPE_DIRECT = "direct"
    TYPE_GROUP = "group"

    TYPE_CHOICES = [
        (TYPE_DIRECT, "Direct"),
        (TYPE_GROUP, "Group"),
    ]

    conversation_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        db_index=True,
    )
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="messaging/group_images/", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_conversations",
    )
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["conversation_type"]),
            models.Index(fields=["last_message_at"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return f"Conversation<{self.id}>"

    @property
    def is_direct(self):
        return self.conversation_type == self.TYPE_DIRECT

    @property
    def is_group(self):
        return self.conversation_type == self.TYPE_GROUP

    def clean(self):
        if self.conversation_type == self.TYPE_DIRECT and self.title:
            raise ValidationError({
                "title": "Direct conversations cannot have a title."
            })


class ConversationParticipant(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_participations",
    )
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    last_read_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    last_read_at = models.DateTimeField(null=True, blank=True)

    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_participant",
            ),
        ]
        indexes = [
            models.Index(fields=["conversation", "user"]),
            models.Index(fields=["user"]),
            models.Index(fields=["conversation"]),
        ]

    def __str__(self):
        return f"{self.user_id} in {self.conversation_id}"


class Message(SoftDeleteModel):
    TYPE_TEXT = "text"
    TYPE_IMAGE = "image"
    TYPE_VIDEO = "video"
    TYPE_FILE = "file"
    TYPE_STORY_REPLY = "story_reply"

    TYPE_CHOICES = [
        (TYPE_TEXT, "Text"),
        (TYPE_IMAGE, "Image"),
        (TYPE_VIDEO, "Video"),
        (TYPE_FILE, "File"),
        (TYPE_STORY_REPLY, "Story Reply"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    message_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_TEXT,
        db_index=True,
    )
    text = models.TextField(blank=True)

    attachment = models.FileField(
        upload_to=message_attachment_upload_to,
        null=True,
        blank=True,
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    story = models.ForeignKey(
        "stories.Story",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reply_messages",
    )

    deleted_for_everyone = models.BooleanField(default=False)
    deleted_for_everyone_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
            models.Index(fields=["message_type"]),
            models.Index(fields=["deleted_at"]),
            models.Index(fields=["conversation", "deleted_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"Message<{self.id}>"

    def clean(self):
        if self.message_type == self.TYPE_TEXT and not self.text.strip():
            raise ValidationError("Text message must contain text.")

        if self.message_type in [self.TYPE_IMAGE, self.TYPE_VIDEO, self.TYPE_FILE] and not self.attachment:
            raise ValidationError("Attachment is required for this message type.")

        if self.message_type == self.TYPE_STORY_REPLY and not self.story:
            raise ValidationError("Story is required for story reply messages.")

    def soft_delete_for_everyone(self):
        now = timezone.now()
        self.deleted_for_everyone = True
        self.deleted_for_everyone_at = now
        self.deleted_at = now
        self.text = ""
        self.attachment = None
        self.file_name = ""
        self.file_size = None
        self.mime_type = ""
        self.save(
            update_fields=[
                "deleted_for_everyone",
                "deleted_for_everyone_at",
                "deleted_at",
                "text",
                "attachment",
                "file_name",
                "file_size",
                "mime_type",
                "updated_at",
            ]
        )


class MessageRecipientStatus(TimeStampedModel):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="recipient_statuses",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_recipient_statuses",
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Message Recipient Status"
        verbose_name_plural = "Message Recipient Statuses"

        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_message_recipient_status",
            )
        ]
        indexes = [
            models.Index(fields=["message", "user"]),
            models.Index(fields=["user", "read_at"]),
            models.Index(fields=["user", "seen_at"]),
        ]

    def __str__(self):
        return f"message={self.message_id}, user={self.user_id}"


class MessageUserState(TimeStampedModel):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="user_states",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_user_states",
    )
    deleted_for_me_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Message User State"
        verbose_name_plural = "Message User States"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_message_user_state",
            )
        ]
        indexes = [
            models.Index(fields=["message", "user"]),
            models.Index(fields=["user", "deleted_for_me_at"]),
        ]

    def __str__(self):
        return f"message={self.message_id}, user={self.user_id}"
