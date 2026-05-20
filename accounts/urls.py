from django.urls import path

from accounts.views import RequestOTPView, VerifyOTPView, LogoutView, MeView, CustomTokenRefreshView, CustomTokenVerifyView

app_name = "accounts"

urlpatterns = [
    path('otp/request/', RequestOTPView.as_view(), name='otp-request'),
    path('otp/verify/', VerifyOTPView.as_view(), name='otp-verify'),

    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),


    path('logout/', LogoutView.as_view(), name='logout'),

    path("me/", MeView.as_view(), name="me"),
]
