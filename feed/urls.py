from django.urls import path

from .views import (
    ExploreListView,
    FeedListView,
    HashtagSearchView,
    PostSearchView,
    UserSearchView,
)


app_name = "feed"

urlpatterns = [
    path("", FeedListView.as_view(), name="feed-list"),
    path("explore/", ExploreListView.as_view(), name="explore-list"),
    path("search/users/", UserSearchView.as_view(), name="search-users"),
    path("search/posts/", PostSearchView.as_view(), name="search-posts"),
    path("search/hashtags/", HashtagSearchView.as_view(), name="search-hashtags"),
]
