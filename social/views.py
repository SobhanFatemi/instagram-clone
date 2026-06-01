from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import Follow, Block
from .serializers import (
    BasicUserSerializer,
    BlockSerializer,
    FollowSerializer,
    SocialActionResponseSerializer,
)


User = get_user_model()


def users_blocked_by_or_blocking(user):
    blocked_ids = Block.objects.filter(
        blocker=user
    ).values_list("blocked_id", flat=True)

    blocking_me_ids = Block.objects.filter(
        blocked=user
    ).values_list("blocker_id", flat=True)

    return set(blocked_ids) | set(blocking_me_ids)


@extend_schema_view(
    list=extend_schema(
        tags=["Social"],
        summary="Social root",
        responses={200: SocialActionResponseSerializer},
    )
)
class SocialViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(
            {"detail": "Social API is working."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Follow"],
        summary="Follow user",
        request=None,
        responses={
            201: FollowSerializer,
            200: SocialActionResponseSerializer,
            400: SocialActionResponseSerializer,
            403: SocialActionResponseSerializer,
        },
    )
    @action(detail=False, methods=["post"], url_path=r"follow/(?P<user_id>\d+)")
    def follow(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        blocked_exists = Block.objects.filter(
            Q(blocker=request.user, blocked=target_user)
            | Q(blocker=target_user, blocked=request.user)
        ).exists()

        if blocked_exists:
            return Response(
                {"detail": "You cannot follow this user because one of you has blocked the other."},
                status=status.HTTP_403_FORBIDDEN,
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user,
        )

        if not created:
            return Response(
                {"detail": "You are already following this user."},
                status=status.HTTP_200_OK,
            )

        services.invalidate_follow_counts(request.user, target_user)

        serializer = FollowSerializer(
            follow,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Follow"],
        summary="Unfollow user",
        request=None,
        responses={
            200: SocialActionResponseSerializer,
            404: SocialActionResponseSerializer,
        },
    )
    @action(detail=False, methods=["post"], url_path=r"unfollow/(?P<user_id>\d+)")
    def unfollow(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        follow = Follow.objects.filter(
            follower=request.user,
            following=target_user,
        ).first()

        if not follow:
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        follow.delete()

        services.invalidate_follow_counts(request.user, target_user)

        return Response(
            {"detail": "User unfollowed successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Follow"],
        summary="List followers of a user",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path=r"followers/(?P<user_id>\d+)")
    def followers(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        hidden_user_ids = users_blocked_by_or_blocking(request.user)

        followers_ids = Follow.objects.filter(
            following=target_user
        ).values_list("follower_id", flat=True)

        users = User.objects.filter(
            id__in=followers_ids
        ).exclude(
            id__in=hidden_user_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Follow"],
        summary="List users followed by a user",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path=r"following/(?P<user_id>\d+)")
    def following(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        hidden_user_ids = users_blocked_by_or_blocking(request.user)

        following_ids = Follow.objects.filter(
            follower=target_user
        ).values_list("following_id", flat=True)

        users = User.objects.filter(
            id__in=following_ids
        ).exclude(
            id__in=hidden_user_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Follow"],
        summary="List my followers",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="my-followers")
    def my_followers(self, request):
        hidden_user_ids = users_blocked_by_or_blocking(request.user)

        followers_ids = Follow.objects.filter(
            following=request.user
        ).values_list("follower_id", flat=True)

        users = User.objects.filter(
            id__in=followers_ids
        ).exclude(
            id__in=hidden_user_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Follow"],
        summary="List users I follow",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="my-following")
    def my_following(self, request):
        hidden_user_ids = users_blocked_by_or_blocking(request.user)

        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list("following_id", flat=True)

        users = User.objects.filter(
            id__in=following_ids
        ).exclude(
            id__in=hidden_user_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Follow"],
        summary="Show mutual followers with a user",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path=r"mutual-followers/(?P<user_id>\d+)")
    def mutual_followers(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        hidden_user_ids = users_blocked_by_or_blocking(request.user)

        my_followers_ids = Follow.objects.filter(
            following=request.user
        ).values_list("follower_id", flat=True)

        target_followers_ids = Follow.objects.filter(
            following=target_user
        ).values_list("follower_id", flat=True)

        mutual_ids = set(my_followers_ids).intersection(set(target_followers_ids))

        users = User.objects.filter(
            id__in=mutual_ids
        ).exclude(
            id__in=hidden_user_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Block"],
        summary="Block user",
        description="Blocking removes follow relations between both users.",
        request=None,
        responses={
            201: BlockSerializer,
            200: SocialActionResponseSerializer,
            400: SocialActionResponseSerializer,
        },
    )
    @action(detail=False, methods=["post"], url_path=r"block/(?P<user_id>\d+)")
    def block(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user:
            return Response(
                {"detail": "You cannot block yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        block, created = Block.objects.get_or_create(
            blocker=request.user,
            blocked=target_user,
        )

        Follow.objects.filter(
            Q(follower=request.user, following=target_user)
            | Q(follower=target_user, following=request.user)
        ).delete()

        services.invalidate_follow_counts(request.user, target_user)

        if not created:
            return Response(
                {"detail": "You have already blocked this user."},
                status=status.HTTP_200_OK,
            )

        serializer = BlockSerializer(
            block,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Block"],
        summary="Unblock user",
        request=None,
        responses={
            200: SocialActionResponseSerializer,
            404: SocialActionResponseSerializer,
        },
    )
    @action(detail=False, methods=["post"], url_path=r"unblock/(?P<user_id>\d+)")
    def unblock(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        block = Block.objects.filter(
            blocker=request.user,
            blocked=target_user,
        ).first()

        if not block:
            return Response(
                {"detail": "You have not blocked this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        block.delete()

        return Response(
            {"detail": "User unblocked successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Block"],
        summary="List users I blocked",
        responses={200: BasicUserSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="blocked-users")
    def blocked_users(self, request):
        blocked_ids = Block.objects.filter(
            blocker=request.user
        ).values_list("blocked_id", flat=True)

        users = User.objects.filter(
            id__in=blocked_ids
        ).order_by("username")

        serializer = BasicUserSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
