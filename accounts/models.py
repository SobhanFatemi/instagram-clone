from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone

from common.models import TimeStampedModel
from .managers import UserManager


class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)

    is_active = models.BooleanField(default=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(email__isnull=False) | Q(phone_number__isnull=False),
                name="user_email_or_phone_required",
            ),
        ]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.username


class AuthOTP(TimeStampedModel):
    PURPOSE_SIGNUP = "signup"
    PURPOSE_LOGIN = "login"
    PURPOSE_RESET = "reset_password"

    PURPOSE_CHOICES = [
        (PURPOSE_SIGNUP, "Signup"),
        (PURPOSE_LOGIN, "Login"),
        (PURPOSE_RESET, "Reset Password"),
    ]

    CHANNEL_EMAIL = "email"
    CHANNEL_PHONE = "phone"

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_PHONE, "Phone"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        null=True,
        blank=True,
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    target_value = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["target_value", "purpose"]),
            models.Index(fields=["channel", "target_value"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["consumed_at"]),
        ]

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self):
        return self.consumed_at is not None

    @property
    def is_usable(self):
        return not self.is_expired and not self.is_consumed

    def __str__(self):
        return f"{self.target_value} - {self.purpose}"


class AuthSession(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_sessions",
    )
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token = models.TextField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_revoked = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Session<{self.user_id}>"
