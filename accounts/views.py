from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from accounts.models import User
from accounts.serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    AddContactOTPRequestSerializer,
    AddContactOTPVerifySerializer,
    LogoutSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
    TokenVerifyRequestSerializer,
    DetailResponseSerializer,
    MeResponseSerializer,
    MeUpdateSerializer,
    VerifyOTPResponseSerializer,

)
from accounts.services.otp_service import (
    create_otp,
    verify_otp,
    OTPError,
    OTPCooldownError,
    CHANNEL_EMAIL,
    CHANNEL_PHONE,
    PURPOSE_LOGIN,
    PURPOSE_SIGNUP,
    PURPOSE_ADD_EMAIL,
    PURPOSE_ADD_PHONE,
)
from accounts.services.rate_limit_service import (
    RateLimitError,
    check_login_rate_limit,
    check_signup_rate_limit,
)
from accounts.services.notification_service import send_otp
from accounts.services.auth_service import (
    get_or_create_user_for_email,
    get_or_create_user_for_phone_number,
)
from accounts.services.token_service import create_tokens_for_user
from accounts.services.user_service import (
    build_me_response,
    set_user_email,
    set_user_phone_number,
)



class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        request=TokenRefreshRequestSerializer,
        responses={200: TokenRefreshResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    @extend_schema(
        tags=["Auth"],
        summary="Verify token",
        request=TokenVerifyRequestSerializer,
        responses={200: OpenApiResponse(description="Token is valid")},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RequestOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RequestOTPSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Request OTP",
        request=RequestOTPSerializer,
        responses={
            200: DetailResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        }
    )
    def post(self, request):
        if request.user.is_authenticated:
            return Response(
                {"detail": "You are already logged in. Please log out first."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        channel = serializer.validated_data["channel"]
        target_value = serializer.validated_data["target_value"].strip()

        if channel == CHANNEL_EMAIL:
            target_value = target_value.lower()
            user = User.objects.filter(email__iexact=target_value).first()
        else:
            user = User.objects.filter(phone_number=target_value).first()

        if user:
            purpose = PURPOSE_LOGIN
        else:
            purpose = PURPOSE_SIGNUP

        identifier = request.META.get("REMOTE_ADDR", "unknown")

        try:
            if purpose == PURPOSE_LOGIN:
                check_login_rate_limit(identifier)
            else:
                check_signup_rate_limit(identifier)
        except RateLimitError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            code = create_otp(
                channel=channel,
                target_value=target_value,
            )
        except OTPCooldownError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        send_otp(
            channel=channel,
            target_value=target_value,
            code=code,
        )

        response_data = {
            "detail": "OTP sent successfully.",
            "purpose": purpose,
        }

        if settings.DEBUG:
            response_data["dev_code"] = code

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Verify OTP",
        request=VerifyOTPSerializer,
        responses={
            200: VerifyOTPResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        channel = serializer.validated_data["channel"]
        target_value = serializer.validated_data["target_value"].strip()
        code = serializer.validated_data["code"]

        if channel == CHANNEL_EMAIL:
            target_value = target_value.lower()

        try:
            verify_otp(
                channel=channel,
                target_value=target_value,
                code=code,
            )
        except OTPError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if channel == CHANNEL_EMAIL:
            user = get_or_create_user_for_email(target_value)
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        elif channel == CHANNEL_PHONE:
            user = get_or_create_user_for_phone_number(target_value)
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])
        else:
            return Response(
                {"detail": "Invalid OTP channel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = create_tokens_for_user(user)

        return Response(
            {
                "detail": "Login successful.",
                "user": {
                    "id": user.id,
                    "email": getattr(user, "email", None),
                    "phone_number": getattr(user, "phone_number", None),
                },
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class RequestContactOTPView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddContactOTPRequestSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Request OTP to add or change email or phone",
        request=AddContactOTPRequestSerializer,
        responses={
            200: DetailResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        channel = serializer.validated_data["channel"]
        target_value = serializer.validated_data["target_value"]

        if channel == CHANNEL_EMAIL:
            purpose = PURPOSE_ADD_EMAIL
        else:
            purpose = PURPOSE_ADD_PHONE

        try:
            code = create_otp(
                channel=purpose,
                target_value=target_value,
            )
        except OTPCooldownError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        send_otp(
            channel=channel,
            target_value=target_value,
            code=code,
        )

        response_data = {
            "detail": "OTP sent successfully.",
            "purpose": purpose,
        }

        if settings.DEBUG:
            response_data["dev_code"] = code

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyContactOTPView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddContactOTPVerifySerializer

    @extend_schema(
        tags=["Auth"],
        summary="Verify OTP to add or change email or phone",
        request=AddContactOTPVerifySerializer,
        responses={
            200: MeResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        channel = serializer.validated_data["channel"]
        target_value = serializer.validated_data["target_value"]
        code = serializer.validated_data["code"]

        if channel == CHANNEL_EMAIL:
            purpose = PURPOSE_ADD_EMAIL
        else:
            purpose = PURPOSE_ADD_PHONE

        try:
            verify_otp(
                channel=purpose,
                target_value=target_value,
                code=code,
            )
        except OTPError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if channel == CHANNEL_EMAIL:
            set_user_email(request.user, target_value)
        else:
            set_user_phone_number(request.user, target_value)

        return Response(build_me_response(request.user), status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Logout",
        request=LogoutSerializer,
        responses={
            200: DetailResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user",
        description="Return authenticated user's profile information.",
        responses={
            200: MeResponseSerializer,
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def get(self, request):
        return Response(build_me_response(request.user), status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Auth"],
        summary="Update current user",
        description="Fully update editable fields of the authenticated user.",
        request=MeUpdateSerializer,
        responses={
            200: MeResponseSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def put(self, request):
        user = request.user
        serializer = MeUpdateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user.username = data.get("username", user.username)
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.save()

        return Response(build_me_response(user), status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Auth"],
        summary="Partially update current user",
        description="Partially update editable fields of the authenticated user.",
        request=MeUpdateSerializer,
        responses={
            200: MeResponseSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def patch(self, request):
        user = request.user
        serializer = MeUpdateSerializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        if "username" in data:
            user.username = data["username"]
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        user.save()

        return Response(build_me_response(user), status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Auth"],
        summary="Delete current user",
        description="Delete the authenticated user's account.",
        responses={
            204: OpenApiResponse(description="User deleted successfully."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)