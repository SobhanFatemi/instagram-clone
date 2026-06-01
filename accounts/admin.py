from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from common.admin import TimestampedAdminMixin
from .models import User, AuthSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "is_phone_verified",
        "date_joined",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "is_phone_verified",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "phone_number",
        "first_name",
        "last_name",
    )
    ordering = ("-id",)

    fieldsets = (
        ("Login Info", {
            "fields": ("username", "password")
        }),
        ("Personal Info", {
            "fields": ("first_name", "last_name", "email", "phone_number")
        }),
        ("Verification", {
            "fields": ("is_email_verified", "is_phone_verified")
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        ("Create User", {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "phone_number",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_superuser",
                "is_email_verified",
                "is_phone_verified",
            ),
        }),
    )


@admin.register(AuthSession)
class AuthSessionAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "short_jti",
        "ip_address",
        "is_revoked",
        "expires_at",
        "revoked_at",
        "created_at",
    )
    list_filter = (
        "is_revoked",
        "created_at",
        "expires_at",
        "revoked_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
        "jti",
        "ip_address",
        "user_agent",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Session Info", {
            "fields": (
                "user",
                "jti",
                "refresh_token",
            )
        }),
        ("Client Info", {
            "fields": (
                "user_agent",
                "ip_address",
            )
        }),
        ("Status", {
            "fields": (
                "is_revoked",
                "expires_at",
                "revoked_at",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    @admin.display(description="JTI")
    def short_jti(self, obj):
        if not obj.jti:
            return "-"
        return obj.jti[:12]
