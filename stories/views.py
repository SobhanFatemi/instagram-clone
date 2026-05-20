from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from social.models import Block, Follow
from .models import Story, StoryComment, StoryView
from .serializers import (
    StoryCommentCreateSerializer,
    StoryCommentSerializer,
    StoryCreateSerializer,
    StoryDetailSerializer,
    StoryGroupSerializer,
    StoryListSerializer,
    StoryViewerSerializer,
)


STORY_MULTIPART_REQUEST_SCHEMA = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "media_type": {
                "type": "string",
                "enum": ["image", "video"],
                "example": "image",
            },
            "file": {
                "type": "string",
                "format": "binary",
            },
            "text": {
                "type": "string",
                "example": "My story text",
            },
        },
        "required": ["media_type", "file"],
    }
}


def active_stories_queryset():
    return Story.objects.filter(
        expires_at__gt=timezone.now(),
        deleted_at__isnull=True,
    ).select_related("user")


def get_blocked_user_ids(user):
    blocked_user_ids = Block.objects.filter(
        blocker=user
    ).values_list("blocked_id", flat=True)

    blocked_by_user_ids = Block.objects.filter(
        blocked=user
    ).values_list("blocker_id", flat=True)

    return set(blocked_user_ids) | set(blocked_by_user_ids)


def get_visible_story_user_ids(user):
    following_ids = Follow.objects.filter(
        follower=user
    ).values_list("following_id", flat=True)

    return list(following_ids) + [user.id]


@extend_schema_view(
    list=extend_schema(
        tags=["Stories"],
        summary="Story feed",
        responses={200: StoryGroupSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Stories"],
        summary="Retrieve story",
        responses={200: StoryDetailSerializer},
    ),
    create=extend_schema(
        tags=["Stories"],
        summary="Create story",
        description="Create an image or video story using multipart/form-data.",
        request=STORY_MULTIPART_REQUEST_SCHEMA,
        responses={201: StoryDetailSerializer},
    ),
    destroy=extend_schema(
        tags=["Stories"],
        summary="Delete story",
        responses={204: None},
    ),
)
class StoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        queryset = active_stories_queryset().annotate(
            views_count=Count("views", distinct=True),
            is_viewed=Exists(
                StoryView.objects.filter(
                    story_id=OuterRef("pk"),
                    viewer=user,
                )
            ),
        )

        if self.action in ["list", "retrieve", "mark_viewed"]:
            visible_user_ids = get_visible_story_user_ids(user)
            blocked_user_ids = get_blocked_user_ids(user)

            queryset = queryset.filter(
                user_id__in=visible_user_ids
            ).exclude(
                user_id__in=blocked_user_ids
            )

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return StoryCreateSerializer
        if self.action == "list":
            return StoryListSerializer
        return StoryDetailSerializer

    def list(self, request, *args, **kwargs):
        user = request.user

        visible_user_ids = get_visible_story_user_ids(user)
        blocked_user_ids = get_blocked_user_ids(user)

        stories = active_stories_queryset().filter(
            user_id__in=visible_user_ids
        ).exclude(
            user_id__in=blocked_user_ids
        ).annotate(
            views_count=Count("views", distinct=True),
            is_viewed=Exists(
                StoryView.objects.filter(
                    story_id=OuterRef("pk"),
                    viewer=user,
                )
            ),
        ).order_by("user_id", "-created_at")

        grouped = {}

        for story in stories:
            user_id = story.user_id

            if user_id not in grouped:
                grouped[user_id] = {
                    "user_id": user_id,
                    "username": story.user.username,
                    "latest_story_created_at": story.created_at,
                    "stories": [],
                }

            if story.created_at > grouped[user_id]["latest_story_created_at"]:
                grouped[user_id]["latest_story_created_at"] = story.created_at

            grouped[user_id]["stories"].append(story)

        result = []
        for item in grouped.values():
            item["stories"] = StoryListSerializer(
                item["stories"],
                many=True,
                context={"request": request},
            ).data
            result.append(item)

        result.sort(
            key=lambda x: x["latest_story_created_at"],
            reverse=True,
        )

        serializer = StoryGroupSerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        story = serializer.save()

        story = Story.objects.filter(pk=story.pk).select_related("user").annotate(
            views_count=Count("views", distinct=True),
            is_viewed=Exists(
                StoryView.objects.filter(
                    story_id=OuterRef("pk"),
                    viewer=request.user,
                )
            ),
        ).first()

        output_serializer = StoryDetailSerializer(
            story,
            context={"request": request},
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        story = self.get_object()
        serializer = StoryDetailSerializer(story, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        story = get_object_or_404(
            Story,
            pk=kwargs["pk"],
            deleted_at__isnull=True,
        )

        if story.user != request.user:
            return Response(
                {"detail": "You do not have permission to delete this story."},
                status=status.HTTP_403_FORBIDDEN,
            )

        story.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Stories"],
        summary="My active stories",
        responses={200: StoryListSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="my")
    def my_stories(self, request):
        stories = active_stories_queryset().filter(
            user=request.user
        ).annotate(
            views_count=Count("views", distinct=True),
            is_viewed=Exists(
                StoryView.objects.filter(
                    story_id=OuterRef("pk"),
                    viewer=request.user,
                )
            ),
        ).order_by("-created_at")

        serializer = StoryListSerializer(
            stories,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Story Views"],
        summary="Mark story as viewed",
        responses={200: None},
    )
    @action(detail=True, methods=["post"], url_path="view")
    def mark_viewed(self, request, pk=None):
        story = self.get_object()

        StoryView.objects.get_or_create(
            story=story,
            viewer=request.user,
        )

        return Response(
            {"detail": "Story marked as viewed."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Story Views"],
        summary="List story viewers",
        responses={200: StoryViewerSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="viewers")
    def viewers(self, request, pk=None):
        story = get_object_or_404(
            Story,
            pk=pk,
            deleted_at__isnull=True,
        )

        if story.user != request.user:
            return Response(
                {"detail": "You do not have permission to view this story's viewers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        viewers = StoryView.objects.filter(
            story=story
        ).select_related("viewer").order_by("-created_at")

        serializer = StoryViewerSerializer(viewers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Story Comments"],
    summary="List and create story comments",
)
class StoryCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StoryCommentCreateSerializer
        return StoryCommentSerializer

    def get_story(self):
        story = get_object_or_404(
            Story,
            pk=self.kwargs["story_id"],
            deleted_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        return story

    def get_queryset(self):
        story = self.get_story()

        return StoryComment.objects.filter(
            story=story,
            parent__isnull=True,
            deleted_at__isnull=True,
        ).select_related("user", "story").prefetch_related(
            Prefetch(
                "replies",
                queryset=StoryComment.objects.filter(
                    deleted_at__isnull=True
                ).select_related("user").order_by("created_at"),
            )
        ).order_by("created_at")

    def list(self, request, *args, **kwargs):
        self.get_story()
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        story = self.get_story()

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(story=story)

        output_serializer = StoryCommentSerializer(
            serializer.instance,
            context={"request": request},
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Story Comments"],
    summary="Delete story comment or reply",
)
class StoryCommentDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StoryCommentSerializer

    def get_object(self):
        return get_object_or_404(
            StoryComment.objects.select_related("user", "story"),
            pk=self.kwargs["comment_id"],
            deleted_at__isnull=True,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        if request.user != comment.user and request.user != comment.story.user:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()

        if comment.parent_id is None:
            replies_qs = StoryComment.objects.filter(
                parent=comment,
                deleted_at__isnull=True,
            )
            replies_qs.update(deleted_at=now)
            comment.deleted_at = now
            comment.save(update_fields=["deleted_at"])
        else:
            comment.deleted_at = now
            comment.save(update_fields=["deleted_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)
