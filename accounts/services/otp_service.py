import random
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from accounts.models import AuthOTP

from django.conf import settings
from django.utils import timezone

from accounts.models import AuthOTP


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5


def generate_otp_code(length=OTP_LENGTH):
    start = 10 ** (length - 1)
    end = (10 ** length) - 1
    return str(random.randint(start, end))


def create_otp(*, user=None, channel, purpose, target_value):
    code = generate_otp_code()

    otp = AuthOTP.objects.create(
        user=user,
        channel=channel,
        purpose=purpose,
        target_value=target_value.lower().strip(),
        code=code,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    return otp



class OTPError(Exception):
    pass


class OTPExpiredError(OTPError):
    pass


class OTPConsumedError(OTPError):
    pass


class OTPInvalidError(OTPError):
    pass


class OTPMaxAttemptsError(OTPError):
    pass


@transaction.atomic
def verify_otp(*, channel, purpose, target_value, code):
    target_value = target_value.lower().strip()

    otp = (
        AuthOTP.objects
        .select_for_update()
        .filter(
            channel=channel,
            purpose=purpose,
            target_value=target_value,
        )
        .order_by('-created_at')
        .first()
    )

    if not otp:
        raise OTPInvalidError("Invalid OTP.")

    if otp.consumed_at is not None:
        raise OTPConsumedError("OTP already used.")

    if timezone.now() >= otp.expires_at:
        raise OTPExpiredError("OTP expired.")

    if otp.attempt_count >= OTP_MAX_ATTEMPTS:
        raise OTPMaxAttemptsError("Maximum OTP attempts exceeded.")

    if otp.code != code:
        otp.attempt_count += 1
        otp.save(update_fields=['attempt_count'])
        raise OTPInvalidError("Invalid OTP.")

    otp.consumed_at = timezone.now()
    otp.save(update_fields=['consumed_at'])

    return otp

