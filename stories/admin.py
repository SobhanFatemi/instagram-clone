from django.contrib import admin

from common.admin import SoftDeleteAdminMixin, TimestampedAdminMixin
from .models import Story, StoryView, StoryComment


class StoryViewInline(admin.TabularInline):
    model = StoryView
    extra = 0
    autocomplete_fields = ("viewer",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("viewer", "created_at", "updated_at")
    show_change_link = True


class StoryCommentInline(admin.TabularInline):
    model = StoryComment
    extra = 0
    autocomplete_fields = ("user", "parent")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    fields = ("user", "parent", "content", "created_at", "updated_at", "deleted_at")
    show_change_link = True


@admin.register(Story)
class StoryAdmin(SoftDeleteAdminMixin, TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "media_type",
        "short_text",
        "expires_at",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "media_type",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    search_fields = (
        "text",
        "user__username",
        "user__email",
    )
    autocomplete_fields = (
        "user",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )
    inlines = [StoryViewInline, StoryCommentInline]

    fieldsets = (
        ("Story Info", {
            "fields": (
                "user",
                "media_type",
                "file",
                "text",
                "expires_at",
            )
        }),
        ("Lifecycle", {
            "fields": (
                "deleted_at",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Text")
    def short_text(self, obj):
        if not obj.text:
            return "-"
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")

    @admin.display(boolean=True, description="Deleted")
    def is_deleted(self, obj):
        return bool(obj.deleted_at)


@admin.register(StoryView)
class StoryViewAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "story",
        "viewer",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "story__text",
        "viewer__username",
        "viewer__email",
        "story__user__username",
        "story__user__email",
    )
    autocomplete_fields = (
        "story",
        "viewer",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("View Info", {
            "fields": (
                "story",
                "viewer",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(StoryComment)
class StoryCommentAdmin(SoftDeleteAdminMixin, TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "story",
        "user",
        "parent",
        "short_content",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
        "deleted_at",
    )
    search_fields = (
        "content",
        "user__username",
        "user__email",
        "story__user__username",
        "story__user__email",
    )
    autocomplete_fields = (
        "story",
        "user",
        "parent",
    )
    ordering = ("created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    fieldsets = (
        ("Comment Info", {
            "fields": (
                "story",
                "user",
                "parent",
                "content",
            )
        }),
        ("Lifecycle", {
            "fields": (
                "deleted_at",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Content")
    def short_content(self, obj):
        if not obj.content:
            return "-"
        return obj.content[:60] + ("..." if len(obj.content) > 60 else "")

    @admin.display(boolean=True, description="Deleted")
    def is_deleted(self, obj):
        return bool(obj.deleted_at)
