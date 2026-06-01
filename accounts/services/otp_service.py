import random
import time

from django.core.cache import cache


OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60

CHANNEL_EMAIL = "email"
CHANNEL_PHONE = "phone"

CHANNEL_CHOICES = [
    (CHANNEL_EMAIL, "Email"),
    (CHANNEL_PHONE, "Phone"),
]

PURPOSE_LOGIN = "login"
PURPOSE_SIGNUP = "signup"
PURPOSE_ADD_EMAIL = "add_email_to_account"
PURPOSE_ADD_PHONE = "add_phone_to_account"


class OTPError(Exception):
    pass


class OTPCooldownError(OTPError):
    pass


def generate_otp_code(length=OTP_LENGTH):
    start = 10 ** (length - 1)
    end = (10 ** length) - 1
    return str(random.randint(start, end))


def normalize_target(target_value):
    return target_value.lower().strip()


def otp_key(channel, target_value):
    return f"otp:{channel}:{normalize_target(target_value)}"


def cooldown_key(target_value):
    return f"otp_resend_cooldown:{normalize_target(target_value)}"


def create_otp(*, channel, target_value):
    target_value = normalize_target(target_value)

    if cache.get(cooldown_key(target_value)):
        raise OTPCooldownError("Please wait before requesting a new code.")

    code = generate_otp_code()

    cache.set(
        otp_key(channel, target_value),
        {
            "code": code,
            "attempts": 0,
            "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        },
        timeout=OTP_EXPIRY_SECONDS,
    )
    cache.set(cooldown_key(target_value), True, timeout=OTP_RESEND_COOLDOWN_SECONDS)

    return code


def verify_otp(*, channel, target_value, code):
    target_value = normalize_target(target_value)
    key = otp_key(channel, target_value)

    data = cache.get(key)

    if not data:
        raise OTPError("Invalid or expired code.")

    remaining = int(data["expires_at"] - time.time())
    if remaining <= 0:
        cache.delete(key)
        raise OTPError("Invalid or expired code.")

    if data["attempts"] >= OTP_MAX_ATTEMPTS:
        cache.delete(key)
        raise OTPError("Too many attempts. Please request a new code.")

    if data["code"] != code:
        data["attempts"] += 1
        cache.set(key, data, timeout=remaining)
        raise OTPError("Invalid code.")

    cache.delete(key)
    return True
