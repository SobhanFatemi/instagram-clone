from django.contrib import admin
from django.utils.html import format_html

from common.admin import TimestampedAdminMixin, SoftDeleteAdminMixin
from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageRecipientStatus,
    MessageUserState,
)

class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    readonly_fields = ("joined_at", "last_read_at")
    autocomplete_fields = ("user", "last_read_message")

@admin.register(Conversation)
class ConversationAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "conversation_type",
        "title",
        "created_by",
        "last_message_at",
        "created_at",
    )
    list_filter = ("conversation_type", "created_at", "last_message_at")
    search_fields = ("title", "created_by__username", "created_by__email")
    ordering = ("-last_message_at", "-created_at")

    readonly_fields = ("created_at", "updated_at",)

    inlines = [ConversationParticipantInline]

    fieldsets = (
        ("Conversation Info", {
            "fields": (
                "conversation_type",
                "title",
                "image",
                "created_by",
                "last_message_at",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "user",
        "is_admin",
        "joined_at",
        "last_read_message",
        "last_read_at",
        "hidden_at",
        "created_at",
    )
    list_filter = ("is_admin", "hidden_at", "created_at")
    search_fields = ("conversation__id", "user__username", "user__email")
    autocomplete_fields = ("conversation", "user", "last_read_message")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

class MessageRecipientStatusInline(admin.TabularInline):
    model = MessageRecipientStatus
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("delivered_at", "read_at", "seen_at", "created_at", "updated_at")

class MessageUserStateInline(admin.TabularInline):
    model = MessageUserState
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("deleted_for_me_at", "created_at", "updated_at")

@admin.register(Message)
class MessageAdmin(TimestampedAdminMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "message_type",
        "short_text",
        "deleted_for_everyone",
        "deleted_at",
        "created_at",
    )
    list_filter = (
        "message_type",
        "deleted_for_everyone",
        "created_at",
        "deleted_at",
    )
    search_fields = (
        "id",
        "conversation__id",
        "sender__username",
        "text",
        "file_name",
        "mime_type",
    )
    autocomplete_fields = ("conversation", "sender", "story")
    ordering = ("-created_at",)

    readonly_fields = (
        "created_at", "updated_at",
        "deleted_at", "deleted_for_everyone_at",
    )

    inlines = [
        MessageRecipientStatusInline,
        MessageUserStateInline,
    ]

    fieldsets = (
        ("Message Info", {
            "fields": (
                "conversation",
                "sender",
                "message_type",
                "text",
                "attachment",
                "file_name",
                "file_size",
                "mime_type",
                "story",
            )
        }),
        ("Deletion", {
            "fields": (
                "deleted_for_everyone",
                "deleted_for_everyone_at",
                "deleted_at",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    @admin.display(description="Preview")
    def short_text(self, obj):
        if obj.text:
            return obj.text[:30] + ("..." if len(obj.text) > 30 else "")
        if obj.attachment:
            return f"Attachment: {obj.file_name}"
        return "-"

@admin.register(MessageRecipientStatus)
class MessageRecipientStatusAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "user",
        "delivered_at",
        "read_at",
        "seen_at",
        "created_at",
    )
    list_filter = ("delivered_at", "read_at", "seen_at", "created_at")
    search_fields = ("message__id", "user__username", "user__email")
    autocomplete_fields = ("message", "user")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

@admin.register(MessageUserState)
class MessageUserStateAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "user",
        "deleted_for_me_at",
        "created_at",
    )
    list_filter = ("deleted_for_me_at", "created_at")
    search_fields = ("message__id", "user__username", "user__email")
    autocomplete_fields = ("message", "user")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")
