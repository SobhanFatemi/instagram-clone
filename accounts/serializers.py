from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User
from accounts.services.otp_service import (
    CHANNEL_CHOICES,
    CHANNEL_EMAIL,
    CHANNEL_PHONE,
)


def validate_phone_number(value):
    value = value.strip()

    if not value.isdigit():
        raise serializers.ValidationError("Phone number must contain only digits.")

    if not value.startswith("09"):
        raise serializers.ValidationError("Phone number must start with 09.")

    if len(value) != 11:
        raise serializers.ValidationError("Phone number must be 11 digits.")

    return value


def validate_otp_code(value):
    value = value.strip()

    if not value.isdigit():
        raise serializers.ValidationError("OTP code must contain only digits.")

    if len(value) != 6:
        raise serializers.ValidationError("OTP code must be 6 digits.")

    return value


class RequestOTPSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    target_value = serializers.CharField(max_length=255)

    def validate(self, attrs):
        channel = attrs["channel"]
        target_value = attrs["target_value"].strip()

        if channel == CHANNEL_EMAIL:
            try:
                validate_email(target_value)
            except DjangoValidationError:
                raise serializers.ValidationError({
                    "target_value": "Enter a valid email address."
                })

            target_value = target_value.lower()

        elif channel == CHANNEL_PHONE:
            try:
                target_value = validate_phone_number(target_value)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    "target_value": e.detail
                })

        attrs["target_value"] = target_value
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    target_value = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        channel = attrs["channel"]
        target_value = attrs["target_value"].strip()
        code = attrs["code"].strip()

        if channel == CHANNEL_EMAIL:
            try:
                validate_email(target_value)
            except DjangoValidationError:
                raise serializers.ValidationError({
                    "target_value": "Enter a valid email address."
                })

            target_value = target_value.lower()

        elif channel == CHANNEL_PHONE:
            try:
                target_value = validate_phone_number(target_value)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    "target_value": e.detail
                })

        try:
            code = validate_otp_code(code)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({
                "code": e.detail
            })

        attrs["target_value"] = target_value
        attrs["code"] = code
        return attrs


class AddContactOTPRequestSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    target_value = serializers.CharField(max_length=255)

    def validate(self, attrs):
        channel = attrs["channel"]
        target_value = attrs["target_value"].strip()
        user = self.context["request"].user

        if channel == CHANNEL_EMAIL:
            try:
                validate_email(target_value)
            except DjangoValidationError:
                raise serializers.ValidationError({
                    "target_value": "Enter a valid email address."
                })

            target_value = target_value.lower()

            if User.objects.filter(email__iexact=target_value).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "target_value": "This email is already in use."
                })

        elif channel == CHANNEL_PHONE:
            try:
                target_value = validate_phone_number(target_value)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    "target_value": e.detail
                })

            if User.objects.filter(phone_number=target_value).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "target_value": "This phone number is already in use."
                })

        attrs["target_value"] = target_value
        return attrs


class AddContactOTPVerifySerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    target_value = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        channel = attrs["channel"]
        target_value = attrs["target_value"].strip()
        code = attrs["code"].strip()
        user = self.context["request"].user

        if channel == CHANNEL_EMAIL:
            try:
                validate_email(target_value)
            except DjangoValidationError:
                raise serializers.ValidationError({
                    "target_value": "Enter a valid email address."
                })

            target_value = target_value.lower()

            if User.objects.filter(email__iexact=target_value).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "target_value": "This email is already in use."
                })

        elif channel == CHANNEL_PHONE:
            try:
                target_value = validate_phone_number(target_value)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    "target_value": e.detail
                })

            if User.objects.filter(phone_number=target_value).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "target_value": "This phone number is already in use."
                })

        try:
            code = validate_otp_code(code)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({
                "code": e.detail
            })

        attrs["target_value"] = target_value
        attrs["code"] = code
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class TokenVerifyRequestSerializer(serializers.Serializer):
    token = serializers.CharField()


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField(allow_null=True, required=False)
    last_name = serializers.CharField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    phone_number = serializers.CharField(allow_null=True, required=False)
    is_active = serializers.BooleanField()
    is_generated_username = serializers.BooleanField(required=False)


class MeUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")

        user = self.context["request"].user
        if User.objects.filter(username__iexact=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
class UserInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField(allow_null=True, required=False)
    phone_number = serializers.CharField(allow_null=True, required=False)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class VerifyOTPResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = UserInfoSerializer()
    tokens = TokenPairSerializer()
