from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import Notification
from common.admin import TimestampedAdminMixin, SoftDeleteAdminMixin


@admin.register(Notification)
class NotificationAdmin(
    TimestampedAdminMixin,
    SoftDeleteAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "id",
        "recipient",
        "actor",
        "notification_type",
        "is_read",
        "target_object",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
        "deleted_at",
    )

    search_fields = (
        "recipient__username",
        "recipient__email",
        "actor__username",
        "actor__email",
        "message",
    )

    readonly_fields = (
        "target",
        "created_at",
        "updated_at",
        "deleted_at",
    )

    ordering = ("-created_at",)

    def target_object(self, obj):
        return str(obj.target) if obj.target else "-"
    target_object.short_description = "Target"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "recipient",
            "actor",
            "target_content_type",
        )