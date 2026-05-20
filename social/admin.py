from django.contrib import admin

from common.admin import TimestampedAdminMixin
from .models import Follow, Block


@admin.register(Follow)
class FollowAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "follower",
        "following",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "follower__username",
        "follower__email",
        "following__username",
        "following__email",
    )
    autocomplete_fields = (
        "follower",
        "following",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Relation", {
            "fields": (
                "follower",
                "following",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(Block)
class BlockAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "blocker",
        "blocked",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "blocker__username",
        "blocker__email",
        "blocked__username",
        "blocked__email",
    )
    autocomplete_fields = (
        "blocker",
        "blocked",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Relation", {
            "fields": (
                "blocker",
                "blocked",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
