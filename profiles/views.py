from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema

from .models import Profile
from .serializers import ProfileSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    @extend_schema(
        tags=["Profiles"],
        summary="Get my profile",
        description="Retrieve the authenticated user's profile.",
        responses={200: ProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Profiles"],
        summary="Update my profile",
        description="Fully update the authenticated user's profile.",
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=["Profiles"],
        summary="Partially update my profile",
        description="Partially update the authenticated user's profile.",
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ProfileByUsernameView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        username = self.kwargs.get("username")

        profile = get_object_or_404(
            Profile.objects.select_related("user"),
            user__username=username,
        )

        if not profile.is_active:
            raise Http404("Profile not found")

        return profile

    @extend_schema(
        tags=["Profiles"],
        summary="Get profile by username",
        description="Retrieve a public profile by username.",
        responses={200: ProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
