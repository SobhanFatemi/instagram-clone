from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StoryCommentDetailView,
    StoryCommentListCreateView,
    StoryViewSet,
)

app_name = "stories"

router = DefaultRouter()
router.register("", StoryViewSet, basename="stories")

urlpatterns = [
    path("", include(router.urls)),
    path("<int:story_id>/comments/", StoryCommentListCreateView.as_view(), name="story-comments"),
    path("comments/<int:comment_id>/", StoryCommentDetailView.as_view(), name="story-comment-detail"),
]
