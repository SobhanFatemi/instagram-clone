from django.contrib import admin
from django.utils.html import format_html

from common.admin import TimestampedAdminMixin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "display_name",
        "avatar_preview",
        "is_private",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_private",
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "display_name",
        "bio",
        "user__username",
        "user__email",
        "user__phone_number",
    )

    autocomplete_fields = (
        "user",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "avatar_preview",
    )

    fieldsets = (
        ("User", {
            "fields": (
                "user",
            )
        }),
        ("Profile Info", {
            "fields": (
                "display_name",
                "bio",
                "avatar",
                "avatar_preview",
            )
        }),
        ("Privacy / Status", {
            "fields": (
                "is_private",
                "is_active",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="45" height="45" '
                'style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "-"
