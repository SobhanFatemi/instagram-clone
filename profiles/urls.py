from django.urls import path

from .views import MyProfileView, ProfileByUsernameView

app_name = "profiles"

urlpatterns = [
    path("me/", MyProfileView.as_view(), name="my-profile"),
    path("<str:username>/", ProfileByUsernameView.as_view(), name="profile-by-username"),
]
