# accounts/services/notification_service.py

from django.conf import settings
from django.core.mail import send_mail


class UnsupportedOTPChannelError(Exception):
    pass


def send_otp(channel, target_value, code):
    if channel == "email":
        return send_otp_email(
            email=target_value,
            code=code,
        )

    if channel == "sms":
        return send_otp_sms(
            phone_number=target_value,
            code=code,
        )

    raise UnsupportedOTPChannelError(f"Unsupported OTP channel: {channel}")


def send_otp_email(email, code):
    subject = "Your verification code"
    message = f"Your verification code is: {code}"

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return {
        "channel": "email",
        "target": email,
        "sent": True,
    }


def send_otp_sms(phone_number, code):
    if settings.DEBUG:
        print(f"SMS OTP for {phone_number}: {code}")
        return {
            "channel": "sms",
            "target": phone_number,
            "sent": True,
            "debug": True,
        }

    raise NotImplementedError("SMS provider is not configured yet.")
