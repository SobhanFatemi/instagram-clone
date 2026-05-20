from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.services import create_notification

from social.models import Block
from messaging.models import Conversation


def users_are_blocked(user1, user2):
    if not user1 or not user2:
        return False

    return Block.objects.filter(
        blocker=user1,
        blocked=user2,
    ).exists() or Block.objects.filter(
        blocker=user2,
        blocked=user1,
    ).exists()


@receiver(post_save, sender="social.Follow")
def create_follow_notification(sender, instance, created, **kwargs):
    if not created:
        return

    follower = instance.follower
    following = instance.following

    if users_are_blocked(follower, following):
        return

    create_notification(
        recipient=following,
        actor=follower,
        notification_type=Notification.NotificationType.FOLLOW,
        target=instance,
        message=f"{follower.username} started following you.",
        deduplicate=True,
    )


@receiver(post_save, sender="posts.PostLike")
def create_like_notification(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    post = instance.post
    post_owner = post.author

    if users_are_blocked(user, post_owner):
        return

    create_notification(
        recipient=post_owner,
        actor=user,
        notification_type=Notification.NotificationType.LIKE,
        target=post,
        message=f"{user.username} liked your post.",
        deduplicate=True,
    )


@receiver(post_save, sender="posts.Comment")
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    post = instance.post
    post_owner = post.author

    if users_are_blocked(user, post_owner):
        return

    create_notification(
        recipient=post_owner,
        actor=user,
        notification_type=Notification.NotificationType.COMMENT,
        target=instance,
        message=f"{user.username} commented on your post.",
        deduplicate=False,
    )

@receiver(post_save, sender="messaging.Message")
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return

    message = instance
    conversation = message.conversation
    sender_user = message.sender

    participants = conversation.participants.exclude(user=sender_user).select_related("user")

    if conversation.conversation_type == Conversation.TYPE_DIRECT:
        text = f"{sender_user.username} sent you a message."
    else:
        group_name = conversation.name or "the group"
        text = f"{sender_user.username} sent a message in {group_name}."

    for participant in participants:
        recipient = participant.user

        if users_are_blocked(sender_user, recipient):
            continue

        create_notification(
            recipient=recipient,
            actor=sender_user,
            notification_type=Notification.NotificationType.MESSAGE,
            target=message,
            message=text,
            deduplicate=False,
        )
