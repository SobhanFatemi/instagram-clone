from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

admin.site.site_header = "Social Backend Admin"
admin.site.site_title = "Social Backend Admin"
admin.site.index_title = "Dashboard"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path('api/auth/', include('accounts.urls')),
    path("api/profiles/", include("profiles.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/stories/", include("stories.urls")),
    path("api/social/", include("social.urls")),
    path("api/feed/", include("feed.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/messaging/", include("messaging.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)