from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from social.models import Block
from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageRecipientStatus,

)

User = get_user_model()


@extend_schema_serializer(component_name="MessagingBasicUser")
class BasicUserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "avatar"]

    def get_display_name(self, obj) -> str:
        profile = getattr(obj, "profile", None)
        if profile and hasattr(profile, "display_name"):
            return profile.display_name
        return obj.username

    def get_avatar(self, obj) -> str | None:
        request = self.context.get("request")
        profile = getattr(obj, "profile", None)

        if not profile or not hasattr(profile, "avatar") or not profile.avatar:
            return None

        try:
            url = profile.avatar.url
        except Exception:
            return None

        if request:
            return request.build_absolute_uri(url)

        return url


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = [
            "id",
            "user",
            "is_admin",
            "joined_at",
            "last_read_at",
            "hidden_at",
        ]


class MessageRecipientStatusSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(read_only=True)

    class Meta:
        model = MessageRecipientStatus
        fields = [
            "id",
            "user",
            "delivered_at",
            "read_at",
            "seen_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    sender = BasicUserSerializer(read_only=True)
    recipient_statuses = MessageRecipientStatusSerializer(many=True, read_only=True)
    is_deleted_for_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "message_type",
            "text",
            "attachment",
            "file_name",
            "file_size",
            "mime_type",
            "story",
            "deleted_for_everyone",
            "deleted_for_everyone_at",
            "created_at",
            "updated_at",
            "recipient_statuses",
            "is_deleted_for_me",
        ]
        read_only_fields = [
            "id",
            "sender",
            "deleted_for_everyone",
            "deleted_for_everyone_at",
            "created_at",
            "updated_at",
            "recipient_statuses",
            "is_deleted_for_me",
        ]

    def get_is_deleted_for_me(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_states.filter(
            user=request.user,
            deleted_for_me_at__isnull=False,
        ).exists()


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "message_type",
            "text",
            "attachment",
            "story",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        conversation = attrs.get("conversation")
        message_type = attrs.get("message_type", Message.TYPE_TEXT)
        text = (attrs.get("text") or "").strip()
        attachment = attrs.get("attachment")
        story = attrs.get("story")

        if not ConversationParticipant.objects.filter(
            conversation=conversation,
            user=user,
        ).exists():
            raise serializers.ValidationError("You are not a participant in this conversation.")

        participant_ids = list(
            conversation.participants
            .exclude(user_id=user.id)
            .values_list("user_id", flat=True)
        )

        is_blocked = False
        if participant_ids:
            is_blocked = Block.objects.filter(
                Q(blocker_id=user.id, blocked_id__in=participant_ids) |
                Q(blocker_id__in=participant_ids, blocked_id=user.id)
            ).exists()

        if is_blocked:
            raise serializers.ValidationError(
                "Messaging is not allowed because of a block relationship in this conversation."
            )


        if message_type == Message.TYPE_TEXT and not text:
            raise serializers.ValidationError({"text": "Text is required for text messages."})

        if message_type in [Message.TYPE_IMAGE, Message.TYPE_VIDEO, Message.TYPE_FILE] and not attachment:
            raise serializers.ValidationError({"attachment": "Attachment is required for this message type."})

        if message_type == Message.TYPE_STORY_REPLY and not story:
            raise serializers.ValidationError({"story": "Story is required for story reply messages."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        attachment = validated_data.get("attachment")
        conversation = validated_data["conversation"]

        message = Message.objects.create(
            sender=user,
            **validated_data
        )

        if attachment:
            message.file_name = getattr(attachment, "name", "") or ""
            message.file_size = getattr(attachment, "size", None)
            message.mime_type = getattr(attachment, "content_type", "") or ""
            message.save(update_fields=["file_name", "file_size", "mime_type", "updated_at"])

        now = timezone.now()
        conversation.last_message_at = now
        conversation.save(update_fields=["last_message_at", "updated_at"])

        recipient_ids = conversation.participants.exclude(user=user).values_list("user_id", flat=True)
        MessageRecipientStatus.objects.bulk_create([
            MessageRecipientStatus(
                message=message,
                user_id=recipient_id,
                delivered_at=now,
            )
            for recipient_id in recipient_ids
        ])

        return message


class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "conversation_type",
            "title",
            "image",
            "created_by",
            "last_message_at",
            "created_at",
            "participants",
            "last_message",
            "unread_count",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "last_message_at",
            "created_at",
            "participants",
            "last_message",
            "unread_count",
        ]

    @extend_schema_field(MessageSerializer)
    def get_last_message(self, obj):
        request = self.context.get("request")
        qs = obj.messages.filter(
            deleted_at__isnull=True
        ).select_related("sender", "sender__profile").order_by("-created_at")
        if request and request.user.is_authenticated:
            qs = qs.exclude(
                user_states__user=request.user,
                user_states__deleted_for_me_at__isnull=False,
            )
        message = qs.first()
        if not message:
            return None
        return MessageSerializer(message, context=self.context).data

    def get_unread_count(self, obj) -> int:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0

        participant = obj.participants.filter(user=request.user).first()
        if not participant:
            return 0

        qs = obj.messages.filter(
            deleted_at__isnull=True,
        ).exclude(sender=request.user).exclude(
            user_states__user=request.user,
            user_states__deleted_for_me_at__isnull=False,
        )

        if participant.last_read_at:
            qs = qs.filter(created_at__gt=participant.last_read_at)

        return qs.count()


class CreateDirectConversationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        request = self.context["request"]
        if request.user.id == value:
            raise serializers.ValidationError("You cannot start a direct conversation with yourself.")

        try:
            target_user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        is_blocked = Block.objects.filter(
            Q(blocker=request.user, blocked=target_user) |
            Q(blocker=target_user, blocked=request.user)
        ).exists()
        if is_blocked:
            raise serializers.ValidationError("Messaging is not allowed between these users.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        other_user_id = validated_data["user_id"]

        existing = Conversation.objects.filter(
            conversation_type=Conversation.TYPE_DIRECT,
            participants__user=user,
        ).filter(
            participants__user=other_user_id,
        ).distinct()

        for conv in existing:
            participant_count = conv.participants.count()
            if participant_count == 2:
                return conv

        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            created_by=user,
        )
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=conversation, user=user, is_admin=False),
            ConversationParticipant(conversation=conversation, user_id=other_user_id, is_admin=False),
        ])
        return conversation


class CreateGroupConversationSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        allow_empty=False,
    )

    class Meta:
        model = Conversation
        fields = ["id", "title", "image", "participant_ids"]
        read_only_fields = ["id"]

    def validate_participant_ids(self, value):
        request = self.context["request"]
        ids = list(set(value))

        if request.user.id in ids:
            ids.remove(request.user.id)

        if not ids:
            raise serializers.ValidationError("At least one other participant is required.")

        users_count = User.objects.filter(id__in=ids).count()
        if users_count != len(ids):
            raise serializers.ValidationError("One or more users are invalid.")

        return ids

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        participant_ids = validated_data.pop("participant_ids")

        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_GROUP,
            created_by=request.user,
            **validated_data,
        )

        participants = [
            ConversationParticipant(
                conversation=conversation,
                user=request.user,
                is_admin=True,
            )
        ]
        participants += [
            ConversationParticipant(
                conversation=conversation,
                user_id=user_id,
                is_admin=False,
            )
            for user_id in participant_ids
        ]

        ConversationParticipant.objects.bulk_create(participants)
        return conversation


class MarkConversationReadSerializer(serializers.Serializer):
    last_read_message_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        conversation = self.context["conversation"]

        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user,
        ).first()

        if not participant:
            raise serializers.ValidationError("You are not a participant in this conversation.")

        message_id = attrs.get("last_read_message_id")
        if message_id:
            try:
                message = Message.objects.get(
                    id=message_id,
                    conversation=conversation,
                    deleted_at__isnull=True,
                )
            except Message.DoesNotExist:
                raise serializers.ValidationError({"last_read_message_id": "Invalid message id."})
            attrs["last_read_message"] = message

        attrs["participant"] = participant
        return attrs

    def save(self, **kwargs):
        participant = self.validated_data["participant"]
        last_read_message = self.validated_data.get("last_read_message")
        now = timezone.now()

        participant.last_read_at = now
        if last_read_message:
            participant.last_read_message = last_read_message
        participant.save(update_fields=["last_read_at", "last_read_message", "updated_at"])

        MessageRecipientStatus.objects.filter(
            message__conversation=participant.conversation,
            user=participant.user,
            read_at__isnull=True,
        ).update(read_at=now, seen_at=now, updated_at=now)

        return participant
