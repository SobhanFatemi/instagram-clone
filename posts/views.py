from django.core.cache import cache
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from feed.services import invalidate_feed_cache
from social.models import Block

from .models import Comment, Post, PostLike, SavedPost
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    PostCreateUpdateSerializer,
    PostSerializer,
    SavedPostSerializer,
)


POST_VIEW_DEDUP_SECONDS = 60 * 60 * 6


POST_MULTIPART_REQUEST_SCHEMA = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "caption": {
                "type": "string",
                "example": "My first post",
            },
            "media": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "binary",
                },
            },
            "hashtags": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
        },
        "required": ["media"],
    }
}


def exclude_blocked_users_from_posts_queryset(queryset, user):
    if not user or not user.is_authenticated:
        return queryset

    blocked_user_ids = Block.objects.filter(
        blocker=user,
    ).values_list("blocked_id", flat=True)

    users_who_blocked_me_ids = Block.objects.filter(
        blocked=user,
    ).values_list("blocker_id", flat=True)

    return queryset.exclude(
        author_id__in=blocked_user_ids,
    ).exclude(
        author_id__in=users_who_blocked_me_ids,
    )


@extend_schema_view(
    list=extend_schema(
        tags=["Posts"],
        summary="List posts",
        parameters=[
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter posts by author user id",
            ),
        ],
        responses={200: PostSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Posts"],
        summary="Retrieve post",
        responses={200: PostSerializer},
    ),
    create=extend_schema(
        tags=["Posts"],
        summary="Create post with media",
        request=POST_MULTIPART_REQUEST_SCHEMA,
        responses={201: PostSerializer},
    ),
    update=extend_schema(
        tags=["Posts"],
        summary="Update post and optionally replace media",
        request=POST_MULTIPART_REQUEST_SCHEMA,
        responses={200: PostSerializer},
    ),
    partial_update=extend_schema(
        tags=["Posts"],
        summary="Partially update post and optionally replace media",
        request=POST_MULTIPART_REQUEST_SCHEMA,
        responses={200: PostSerializer},
    ),
    destroy=extend_schema(
        tags=["Posts"],
        summary="Delete post",
        responses={204: None},
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = (
            Post.objects
            .filter(deleted_at__isnull=True)
            .select_related("author", "author__profile")
            .prefetch_related("media_items")
            .order_by("-created_at")
        )

        author_id = self.request.query_params.get("author")
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        return exclude_blocked_users_from_posts_queryset(
            queryset=queryset,
            user=self.request.user,
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PostCreateUpdateSerializer
        return PostSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def _viewer_key(self, request):
        if request.user and request.user.is_authenticated:
            return "user:%s" % request.user.id
        return "ip:%s" % request.META.get("REMOTE_ADDR", "anonymous")

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()

        is_author = (
            request.user.is_authenticated
            and request.user.id == post.author_id
        )

        cache_key = "post_view:%s:%s" % (post.pk, self._viewer_key(request))
        if not is_author and cache.add(cache_key, 1, POST_VIEW_DEDUP_SECONDS):
            Post.objects.filter(pk=post.pk).update(
                view_count=F("view_count") + 1,
            )
            post.refresh_from_db(fields=["view_count"])

        serializer = PostSerializer(
            post,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _prepare_multipart_data(self, request):
        data = request.data.copy()
        media = request.FILES.getlist("media")

        if media:
            data.setlist("media", media)

        return data

    def create(self, request, *args, **kwargs):
        data = self._prepare_multipart_data(request)

        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        post = serializer.save(author=request.user)
        invalidate_feed_cache(request.user)

        output_serializer = PostSerializer(
            post,
            context={"request": request},
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        post = self.get_object()

        data = self._prepare_multipart_data(request)

        serializer = self.get_serializer(
            post,
            data=data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        post = serializer.save()

        output_serializer = PostSerializer(
            post,
            context={"request": request},
        )
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        invalidate_feed_cache(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavePostView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Saved Posts"],
        summary="Save a post",
        description="Save a post for the authenticated user.",
        request=None,
        responses={201: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, deleted_at__isnull=True)

        saved_post, created = SavedPost.objects.get_or_create(
            user=request.user,
            post=post,
        )

        if not created:
            return Response(
                {"detail": "Post already saved."},
                status=status.HTTP_200_OK,
            )

        Post.objects.filter(pk=post.pk).update(save_count=F("save_count") + 1)

        return Response(
            {"detail": "Post saved successfully."},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Saved Posts"],
        summary="Unsave a post",
        description="Remove a post from the authenticated user's saved posts.",
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, deleted_at__isnull=True)

        deleted_count, _ = SavedPost.objects.filter(
            user=request.user,
            post=post,
        ).delete()

        if deleted_count == 0:
            return Response(
                {"detail": "Post was not saved."},
                status=status.HTTP_200_OK,
            )

        Post.objects.filter(pk=post.pk, save_count__gt=0).update(
            save_count=F("save_count") - 1,
        )

        return Response(
            {"detail": "Post unsaved successfully."},
            status=status.HTTP_200_OK,
        )


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Likes"],
        summary="Like a post",
        request=None,
        responses={201: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, deleted_at__isnull=True)

        like, created = PostLike.objects.get_or_create(
            user=request.user,
            post=post,
        )

        if not created:
            return Response(
                {"detail": "Post already liked."},
                status=status.HTTP_200_OK,
            )

        Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)

        return Response(
            {"detail": "Post liked successfully."},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Likes"],
        summary="Unlike a post",
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, deleted_at__isnull=True)

        deleted_count, _ = PostLike.objects.filter(
            user=request.user,
            post=post,
        ).delete()

        if deleted_count == 0:
            return Response(
                {"detail": "Post was not liked."},
                status=status.HTTP_200_OK,
            )

        Post.objects.filter(pk=post.pk, like_count__gt=0).update(
            like_count=F("like_count") - 1,
        )

        return Response(
            {"detail": "Post unliked successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Saved Posts"],
    summary="List my saved posts",
    description="Return all posts saved by the authenticated user.",
    responses={200: SavedPostSerializer(many=True)},
)
class SavedPostListView(generics.ListAPIView):
    serializer_class = SavedPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            SavedPost.objects
            .filter(
                user=self.request.user,
                post__deleted_at__isnull=True,
            )
            .select_related("post", "post__author", "post__author__profile")
            .prefetch_related("post__media_items")
            .order_by("-created_at")
        )


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_post(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs["post_id"],
            deleted_at__isnull=True,
        )

    def get_queryset(self):
        post = self.get_post()
        return (
            Comment.objects
            .filter(
                post=post,
                parent__isnull=True,
                deleted_at__isnull=True,
            )
            .select_related("user", "user__profile", "post")
            .prefetch_related("replies__user", "replies__user__profile")
            .order_by("created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["post"] = self.get_post()
        return context

    @extend_schema(
        tags=["Comments"],
        summary="List comments of a post",
        responses={200: CommentSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Comments"],
        summary="Create a comment on a post",
        request=CommentCreateSerializer,
        responses={201: CommentSerializer},
    )
    def post(self, request, *args, **kwargs):
        post = self.get_post()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save(
            user=request.user,
            post=post,
        )

        Post.objects.filter(pk=post.pk).update(comment_count=F("comment_count") + 1)

        output_serializer = CommentSerializer(comment, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Comment.objects
            .filter(deleted_at__isnull=True)
            .select_related("user", "user__profile", "post", "parent")
        )

    def get_object(self):
        comment = get_object_or_404(
            self.get_queryset(),
            pk=self.kwargs["comment_id"],
        )

        if self.request.method in ["PATCH", "PUT"]:
            if comment.user_id != self.request.user.id:
                self.permission_denied(
                    self.request,
                    message="You do not have permission to update this comment.",
                )

        if self.request.method == "DELETE":
            is_comment_owner = comment.user_id == self.request.user.id
            is_post_owner = comment.post.author_id == self.request.user.id

            if not (is_comment_owner or is_post_owner):
                self.permission_denied(
                    self.request,
                    message="You do not have permission to delete this comment.",
                )

        return comment

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CommentUpdateSerializer
        return CommentSerializer

    @extend_schema(
        tags=["Comments"],
        summary="Retrieve a comment",
        responses={200: CommentSerializer},
    )
    def get(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = CommentSerializer(comment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Comments"],
        summary="Update your comment",
        request=CommentUpdateSerializer,
        responses={200: CommentSerializer},
    )
    def patch(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        output_serializer = CommentSerializer(comment, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Comments"],
        summary="Update your comment",
        request=CommentUpdateSerializer,
        responses={200: CommentSerializer},
    )
    def put(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = self.get_serializer(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        output_serializer = CommentSerializer(comment, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Comments"],
        summary="Delete your comment or a comment under your post",
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        post_id = comment.post_id
        now = timezone.now()

        reply_ids = list(
            comment.replies
            .filter(deleted_at__isnull=True)
            .values_list("id", flat=True)
        )

        total_deleted_comments = 1 + len(reply_ids)

        comment.deleted_at = now
        comment.save(update_fields=["deleted_at", "updated_at"])

        if reply_ids:
            Comment.all_objects.filter(
                id__in=reply_ids,
                deleted_at__isnull=True,
            ).update(
                deleted_at=now,
                updated_at=now,
            )

        post = Post.objects.get(pk=post_id)
        post.comment_count = max(0, post.comment_count - total_deleted_comments)
        post.save(update_fields=["comment_count", "updated_at"])

        return Response(
            {"detail": "Comment deleted successfully."},
            status=status.HTTP_200_OK,
        )
