from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.serializers import PostSerializer
from .serializers import FeedUserSerializer, HashtagSerializer
from .services import (
    get_explore_queryset,
    get_feed_post_ids,
    get_feed_posts_by_ids,
    search_hashtags_queryset,
    search_posts_queryset,
    search_users_queryset,
)


class FeedListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    @extend_schema(
        tags=["Feed"],
        summary="Get home feed",
        description="Returns posts from the authenticated user and users they follow, excluding blocked relationships.",
        responses={200: PostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        post_ids = get_feed_post_ids(request.user)
        page = self.paginate_queryset(post_ids)
        if page is not None:
            posts = get_feed_posts_by_ids(page)
            serializer = self.get_serializer(
                posts,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        posts = get_feed_posts_by_ids(post_ids)
        serializer = self.get_serializer(
            posts,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ExploreListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    @extend_schema(
        tags=["Feed"],
        summary="Get explore feed",
        description="Returns posts from users not followed by the authenticated user, excluding blocked relationships.",
        responses={200: PostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = get_explore_queryset(request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Search"],
        summary="Search users",
        description="Search users by username, first name, or last name. Excludes blocked relationships.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search text for username, first name, or last name",
            ),
        ],
        responses={200: FeedUserSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response([])

        queryset = search_users_queryset(request.user, query)
        serializer = FeedUserSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class PostSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Search"],
        summary="Search posts",
        description="Search posts by caption or hashtag name. Excludes blocked relationships.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search text for post caption or hashtag",
            ),
        ],
        responses={200: PostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response([])

        queryset = search_posts_queryset(request.user, query)
        serializer = PostSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class HashtagSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Search"],
        summary="Search hashtags",
        description="Search hashtags by name.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Hashtag name to search",
            ),
        ],
        responses={200: HashtagSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response([])

        queryset = search_hashtags_queryset(query)
        serializer = HashtagSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
