from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet, MessageViewSet

app_name = "messaging"

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = router.urls
