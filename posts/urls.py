from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentDetailView,
    CommentListCreateView,
    LikePostView,
    PostViewSet,
    SavePostView,
    SavedPostListView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")

urlpatterns = [
    path("saved/", SavedPostListView.as_view(), name="saved-post-list"),
    path("<int:post_id>/save/", SavePostView.as_view(), name="save-post"),
    path("<int:post_id>/like/", LikePostView.as_view(), name="like-post"),
    path("<int:post_id>/comments/", CommentListCreateView.as_view(), name="post-comments"),
    path("<int:comment_id>/", CommentDetailView.as_view(), name="comment-detail"),
    path("", include(router.urls)),
]
