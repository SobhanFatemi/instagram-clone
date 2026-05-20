from django.contrib.contenttypes.models import ContentType

from .models import Notification


def create_notification(
    *,
    recipient,
    actor=None,
    notification_type,
    target=None,
    message="",
    prevent_self_notification=True,
    deduplicate=False,
):

    if recipient is None:
        return None

    if prevent_self_notification and actor and recipient == actor:
        return None

    target_content_type = None
    target_object_id = None

    if target is not None:
        target_content_type = ContentType.objects.get_for_model(target)
        target_object_id = target.pk

    if deduplicate:
        notification, created = Notification.objects.get_or_create(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            target_content_type=target_content_type,
            target_object_id=target_object_id,
            defaults={
                "message": message,
                "is_read": False,
            },
        )

        if not created:
            notification.message = message
            notification.is_read = False
            notification.save(update_fields=["message", "is_read"])

        return notification

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        target_content_type=target_content_type,
        target_object_id=target_object_id,
        message=message,
    )
