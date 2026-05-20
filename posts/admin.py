from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from common.admin import TimestampedAdminMixin, SoftDeleteAdminMixin

from .models import (
    Post,
    PostMedia,
    Hashtag,
    PostHashtag,
    PostLike,
    SavedPost,
    Comment,
)


class PostMediaInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_media = False

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE", False):
                continue

            if form.cleaned_data.get("media"):
                has_media = True
                break

            if form.instance and form.instance.pk:
                has_media = True
                break

        if not has_media:
            raise ValidationError("At least one media item is required.")


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    formset = PostMediaInlineFormSet
    extra = 0
    fields = (
        "media_type",
        "media",
        "thumbnail",
        "sort_order",
        "duration_seconds",
        "created_at",
    )
    readonly_fields = ("created_at",)
    ordering = ("sort_order",)


class PostHashtagInline(admin.TabularInline):
    model = PostHashtag
    extra = 0
    autocomplete_fields = ("hashtag",)
    readonly_fields = ("created_at", "updated_at")


class PostLikeInline(admin.TabularInline):
    model = PostLike
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    can_delete = True


class SavedPostInline(admin.TabularInline):
    model = SavedPost
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    can_delete = True


@admin.register(Post)
class PostAdmin(TimestampedAdminMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "short_caption",
        "like_count",
        "comment_count",
        "save_count",
        "view_count",
        "media_count",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "deleted_at",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "author__username",
        "author__email",
        "author__phone_number",
        "caption",
    )

    autocomplete_fields = ("author",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "media_count",
    )

    ordering = ("-created_at",)

    inlines = (
        PostMediaInline,
        PostHashtagInline,
        PostLikeInline,
        SavedPostInline,
    )

    fieldsets = (
        ("Post Info", {
            "fields": (
                "author",
                "caption",
            )
        }),
        ("Counters", {
            "fields": (
                "like_count",
                "comment_count",
                "save_count",
                "view_count",
                "media_count",
            )
        }),
        ("Soft Delete", {
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

    @admin.display(description="Caption")
    def short_caption(self, obj):
        if not obj.caption:
            return "-"
        return obj.caption[:60] + ("..." if len(obj.caption) > 60 else "")

    @admin.display(description="Media Count")
    def media_count(self, obj):
        if not obj.pk:
            return 0
        return obj.media_items.count()


@admin.register(PostMedia)
class PostMediaAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "media_type",
        "sort_order",
        "media_preview",
        "thumbnail_preview",
        "duration_seconds",
        "created_at",
    )

    list_filter = (
        "media_type",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "post__id",
        "post__author__username",
        "post__author__email",
    )

    autocomplete_fields = ("post",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "media_preview",
        "thumbnail_preview",
    )

    ordering = (
        "post",
        "sort_order",
    )

    fieldsets = (
        ("Media Info", {
            "fields": (
                "post",
                "media_type",
                "media",
                "media_preview",
                "thumbnail",
                "thumbnail_preview",
                "sort_order",
                "duration_seconds",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Media Preview")
    def media_preview(self, obj):
        if not obj.media:
            return "-"

        if obj.media_type == PostMedia.TYPE_IMAGE:
            return format_html(
                '<img src="{}" style="max-width: 120px; max-height: 120px; border-radius: 6px;" />',
                obj.media.url,
            )

        return format_html(
            '<a href="{}" target="_blank">View Media</a>',
            obj.media.url,
        )

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.thumbnail:
            return "-"

        return format_html(
            '<img src="{}" style="max-width: 120px; max-height: 120px; border-radius: 6px;" />',
            obj.thumbnail.url,
        )


@admin.register(Hashtag)
class HashtagAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "post_count",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "post_count",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        ("Hashtag Info", {
            "fields": (
                "name",
                "post_count",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Post Count")
    def post_count(self, obj):
        if not obj.pk:
            return 0
        return obj.hashtag_posts.count()


@admin.register(PostHashtag)
class PostHashtagAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "hashtag",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "post__id",
        "post__author__username",
        "post__author__email",
        "hashtag__name",
    )

    autocomplete_fields = (
        "post",
        "hashtag",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(PostLike)
class PostLikeAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "post_author",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
        "post__id",
        "post__author__username",
        "post__author__email",
    )

    autocomplete_fields = (
        "user",
        "post",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Post Author")
    def post_author(self, obj):
        return obj.post.author if obj.post_id else "-"


@admin.register(SavedPost)
class SavedPostAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "post_author",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
        "post__id",
        "post__author__username",
        "post__author__email",
    )

    autocomplete_fields = (
        "user",
        "post",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Post Author")
    def post_author(self, obj):
        return obj.post.author if obj.post_id else "-"


class CommentReplyInline(admin.TabularInline):
    model = Comment
    fk_name = "parent"
    extra = 0
    fields = (
        "user",
        "post",
        "content",
        "deleted_at",
        "created_at",
    )
    readonly_fields = (
        "deleted_at",
        "created_at",
    )
    autocomplete_fields = (
        "user",
        "post",
    )


@admin.register(Comment)
class CommentAdmin(TimestampedAdminMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "parent",
        "short_content",
        "reply_count",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "deleted_at",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "content",
        "user__username",
        "user__email",
        "user__phone_number",
        "post__id",
        "post__author__username",
        "post__author__email",
        "parent__id",
    )

    autocomplete_fields = (
        "user",
        "post",
        "parent",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "reply_count",
    )

    ordering = (
        "-created_at",
    )

    inlines = (
        CommentReplyInline,
    )

    fieldsets = (
        ("Comment Info", {
            "fields": (
                "user",
                "post",
                "parent",
                "content",
            )
        }),
        ("Replies", {
            "fields": (
                "reply_count",
            )
        }),
        ("Soft Delete", {
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
        return obj.content[:70] + ("..." if len(obj.content) > 70 else "")

    @admin.display(description="Replies")
    def reply_count(self, obj):
        if not obj.pk:
            return 0
        return obj.replies.count()
