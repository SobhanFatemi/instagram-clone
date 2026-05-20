from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification

from .serializers import (
    NotificationSerializer,
    UnreadCountResponseSerializer,
    MarkReadResponseSerializer,
    MarkAllReadResponseSerializer,
    ClearNotificationsResponseSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List notifications",
        description="Return all notifications for the authenticated user, ordered by newest first.",
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        },
    ),
    retrieve=extend_schema(
        tags=["Notifications"],
        summary="Retrieve notification",
        description="Return a single notification that belongs to the authenticated user.",
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Notification not found."),
        },
    ),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .filter(recipient=self.request.user)
            .select_related(
                "recipient",
                "actor",
                "target_content_type",
            )
            .order_by("-created_at")
        )

    @extend_schema(
        tags=["Notifications"],
        summary="Get unread notification count",
        description="Return the number of unread notifications for the authenticated user.",
        responses={
            200: UnreadCountResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        },
    )
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()

        return Response({
            "unread_count": count,
        })

    @extend_schema(
        tags=["Notifications"],
        summary="Mark one notification as read",
        description="Mark a specific notification as read. The notification must belong to the authenticated user.",
        request=None,
        responses={
            200: MarkReadResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        return Response({
            "detail": "Notification marked as read.",
        })

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        description="Mark all unread notifications of the authenticated user as read.",
        request=None,
        responses={
            200: MarkAllReadResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        },
    )
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)

        return Response({
            "detail": "All notifications marked as read.",
            "updated": updated,
        })

    @extend_schema(
        tags=["Notifications"],
        summary="Delete one notification",
        description="Delete a specific notification that belongs to the authenticated user.",
        request=None,
        responses={
            204: OpenApiResponse(description="Notification deleted successfully."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_notification(self, request, pk=None):
        notification = self.get_object()
        notification.delete()

        return Response(
            {
                "detail": "Notification deleted.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        tags=["Notifications"],
        summary="Clear all notifications",
        description="Delete all notifications of the authenticated user.",
        request=None,
        responses={
            200: ClearNotificationsResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        },
    )
    @action(detail=False, methods=["delete"], url_path="clear")
    def clear_all(self, request):
        deleted_count, _ = self.get_queryset().delete()

        return Response({
            "detail": "All notifications cleared.",
            "deleted": deleted_count,
        })
