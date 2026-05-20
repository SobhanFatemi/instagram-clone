from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SocialViewSet

app_name = "social"

router = DefaultRouter()
router.register("", SocialViewSet, basename="social")

urlpatterns = [
    path("", include(router.urls)),
]
