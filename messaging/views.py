from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiRequest,
    extend_schema,
    extend_schema_serializer,
    extend_schema_view,
)

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageRecipientStatus,
    MessageUserState,
)
from .serializers import (
    ConversationSerializer,
    CreateDirectConversationSerializer,
    CreateGroupConversationSerializer,
    MarkConversationReadSerializer,
    MessageSerializer,
    SendMessageSerializer,
)


@extend_schema_serializer(component_name="MessagingDetailResponse")
class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


CONVERSATION_TAG = "Messaging - Conversations"
MESSAGE_TAG = "Messaging - Messages"

CREATE_GROUP_MULTIPART_REQUEST_SCHEMA = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
            },
            "participant_ids": {
                "type": "array",
                "items": {
                    "type": "integer",
                },
            },
            "image": {
                "type": "string",
                "format": "binary",
            },
        },
        "required": ["title", "participant_ids"],
    }
}

SEND_MESSAGE_MULTIPART_REQUEST_SCHEMA = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "conversation": {
                "type": "integer",
                "example": 1,
            },
            "message_type": {
                "type": "string",
                "enum": ["text", "image", "video", "file", "story_reply"],
                "example": "image",
            },
            "text": {
                "type": "string",
            },
            "story": {
                "type": "integer",
                "example": 10,
                "nullable": True,
            },
            "attachment": {
                "type": "string",
                "format": "binary",
            },
        },
        "required": ["conversation", "message_type"],
    }
}



@extend_schema_view(
    list=extend_schema(
        tags=[CONVERSATION_TAG],
        summary="List my conversations",
        description=(
            "Returns all conversations where the authenticated user is a participant. "
            "Hidden conversations are excluded by default. "
            "Pass `hidden=true` to return only the conversations the authenticated user has hidden."
        ),
        parameters=[
            OpenApiParameter(
                name="hidden",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="When true, returns only conversations hidden by the authenticated user.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ConversationSerializer(many=True),
                description="List of conversations.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    ),
    retrieve=extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Retrieve a conversation",
        description=(
            "Returns a single conversation if the authenticated user is a participant."
        ),
        responses={
            200: OpenApiResponse(
                response=ConversationSerializer,
                description="Conversation detail.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Conversation not found."),
        },
    ),
)
class ConversationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Conversation.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Conversation.objects.filter(participants__user=user)
            .prefetch_related("participants__user__profile")
            .distinct()
            .order_by("-last_message_at", "-created_at")
        )

        if self.action == "list" and self.request.query_params.get("hidden") == "true":
            return queryset.filter(
                participants__user=user,
                participants__hidden_at__isnull=False,
            )

        return queryset.exclude(
            participants__user=user,
            participants__hidden_at__isnull=False,
        )

    def get_serializer_class(self):
        if self.action == "create_direct":
            return CreateDirectConversationSerializer
        if self.action == "create_group":
            return CreateGroupConversationSerializer
        if self.action == "mark_read":
            return MarkConversationReadSerializer
        return ConversationSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = ConversationSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ConversationSerializer(
            conversation,
            context={"request": request},
        )
        return Response(serializer.data)

    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Create or get direct conversation",
        description=(
            "Creates a direct one-to-one conversation with another user. "
            "If a direct conversation already exists between the two users, "
            "the existing conversation is returned instead. "
            "Blocked users cannot start a direct conversation."
        ),
        request=CreateDirectConversationSerializer,
        responses={
            201: OpenApiResponse(
                response=ConversationSerializer,
                description="Direct conversation created or existing conversation returned.",
            ),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Create direct conversation",
                value={
                    "user_id": 5,
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Blocked user error",
                value={
                    "user_id": ["Messaging is not allowed between these users."]
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="direct")
    def create_direct(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        output = ConversationSerializer(
            conversation,
            context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Create group conversation",
        description=(
            "Creates a group conversation. "
            "The authenticated user becomes the creator and admin. "
            "You can optionally upload a group image using multipart/form-data."
        ),
        request=CREATE_GROUP_MULTIPART_REQUEST_SCHEMA,
        responses={
            201: OpenApiResponse(
                response=ConversationSerializer,
                description="Group conversation created.",
            ),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
        examples=[
            OpenApiExample(
                name="Create group conversation",
                value={
                    "title": "Backend Team",
                    "participant_ids": [5, 8, 11],
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Create group validation error",
                value={
                    "participant_ids": [
                        "At least one other participant is required."
                    ]
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="group",
        parser_classes=[MultiPartParser, FormParser],
    )
    def create_group(self, request):
        data = request.data.copy()

        image = request.FILES.get("image")
        if image:
            data["image"] = image

        serializer = self.get_serializer(
            data=data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        output = ConversationSerializer(
            conversation,
            context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)



    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Mark conversation as read",
        description=(
            "Marks all unread messages in this conversation as read/seen for the authenticated user. "
            "Optionally accepts `last_read_message_id` to update the participant read cursor."
        ),
        request=MarkConversationReadSerializer,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Conversation marked as read.",
            ),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Conversation not found."),
        },
        examples=[
            OpenApiExample(
                name="Mark conversation read",
                value={
                    "last_read_message_id": 33,
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Conversation marked as read.",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "conversation": conversation,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Conversation marked as read."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Hide conversation for me",
        description=(
            "Hides the conversation only for the authenticated user. "
            "This does not delete the conversation for other participants."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Conversation hidden for current user.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Conversation not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Conversation hidden for you.",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="hide")
    def hide_conversation(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)

        participant = get_object_or_404(
            ConversationParticipant,
            conversation=conversation,
            user=request.user,
        )
        participant.hidden_at = timezone.now()
        participant.save(update_fields=["hidden_at", "updated_at"])

        return Response(
            {"detail": "Conversation hidden for you."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="Restore hidden conversation",
        description=(
            "Restores a conversation previously hidden by the authenticated user."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Conversation restored.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Conversation not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Conversation restored.",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="unhide")
    def unhide_conversation(self, request, pk=None):
        conversation = get_object_or_404(
            Conversation.objects.filter(participants__user=request.user).distinct(),
            pk=pk,
        )

        participant = get_object_or_404(
            ConversationParticipant,
            conversation=conversation,
            user=request.user,
        )
        participant.hidden_at = None
        participant.save(update_fields=["hidden_at", "updated_at"])

        return Response(
            {"detail": "Conversation restored."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=[CONVERSATION_TAG],
        summary="List messages of a conversation",
        description=(
            "Returns messages of a conversation. "
            "Messages deleted for the authenticated user are excluded. "
            "Messages deleted for everyone are also excluded because they are globally soft-deleted."
        ),
        responses={
            200: OpenApiResponse(
                response=MessageSerializer(many=True),
                description="List of messages in the conversation.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Conversation not found."),
        },
    )
    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)

        qs = (
            Message.objects.filter(
                conversation=conversation,
                deleted_at__isnull=True,
            )
            .exclude(
                user_states__user=request.user,
                user_states__deleted_for_me_at__isnull=False,
            )
            .select_related("sender", "sender__profile", "conversation", "story")
            .prefetch_related("recipient_statuses__user")
            .order_by("created_at")
        )

        serializer = MessageSerializer(
            qs,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(
        tags=[MESSAGE_TAG],
        summary="Send message",
        description=(
            "Sends a message in a conversation where the authenticated user is a participant.\n\n"
            "Supported message types:\n"
            "- `text`\n"
            "- `image`\n"
            "- `video`\n"
            "- `file`\n"
            "- `story_reply`\n\n"
            "For image/video/file messages, send the request as `multipart/form-data` "
            "and include the `attachment` field."
        ),
        request=SEND_MESSAGE_MULTIPART_REQUEST_SCHEMA,
        responses={
            201: OpenApiResponse(
                response=MessageSerializer,
                description="Message sent successfully.",
            ),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
        examples=[
            OpenApiExample(
                name="Send text message",
                value={
                    "conversation": 1,
                    "message_type": "text",
                    "text": "Hello!",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Send image message multipart fields",
                description="Use multipart/form-data. Upload the file in `attachment`.",
                value={
                    "conversation": 1,
                    "message_type": "image",
                    "text": "Optional caption",
                    "attachment": "<binary file>",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Send story reply",
                value={
                    "conversation": 1,
                    "message_type": "story_reply",
                    "text": "Nice story!",
                    "story": 10,
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=[MESSAGE_TAG],
        summary="Retrieve a message",
        description=(
            "Returns a single message if the authenticated user is a participant "
            "of the conversation and the message is visible to that user."
        ),
        responses={
            200: OpenApiResponse(
                response=MessageSerializer,
                description="Message detail.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Message not found."),
        },
    ),
)
class MessageViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Message.objects.all()

    def get_queryset(self):
        return (
            Message.objects.filter(
                conversation__participants__user=self.request.user,
                deleted_at__isnull=True,
            )
            .exclude(
                user_states__user=self.request.user,
                user_states__deleted_for_me_at__isnull=False,
            )
            .select_related("sender", "sender__profile", "conversation", "story")
            .prefetch_related("recipient_statuses__user")
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return SendMessageSerializer
        return MessageSerializer

    def create(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        output = MessageSerializer(
            message,
            context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        message = get_object_or_404(self.get_queryset(), pk=pk)

        serializer = MessageSerializer(
            message,
            context={"request": request},
        )
        return Response(serializer.data)

    @extend_schema(
        tags=[MESSAGE_TAG],
        summary="Delete message for me",
        description=(
            "Deletes/hides the selected message only for the authenticated user. "
            "Other participants can still see the message."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Message deleted for current user.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Message not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Message deleted for you.",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="delete-for-me")
    def delete_for_me(self, request, pk=None):
        message = get_object_or_404(
            Message.objects.filter(
                conversation__participants__user=request.user,
            ).distinct(),
            pk=pk,
        )

        state, _ = MessageUserState.objects.get_or_create(
            message=message,
            user=request.user,
        )
        state.deleted_for_me_at = timezone.now()
        state.save(update_fields=["deleted_for_me_at", "updated_at"])

        return Response(
            {"detail": "Message deleted for you."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=[MESSAGE_TAG],
        summary="Delete message for everyone",
        description=(
            "Globally deletes the message for all participants. "
            "Only the sender of the message can delete it for everyone."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Message deleted for everyone.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Only sender can delete message for everyone.",
            ),
            404: OpenApiResponse(description="Message not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Message deleted for everyone.",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Forbidden response",
                value={
                    "detail": "Only sender can delete message for everyone.",
                },
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="delete-for-everyone")
    def delete_for_everyone(self, request, pk=None):
        message = get_object_or_404(
            Message.objects.filter(
                conversation__participants__user=request.user,
                deleted_at__isnull=True,
            ).distinct(),
            pk=pk,
        )

        if message.sender_id != request.user.id:
            return Response(
                {"detail": "Only sender can delete message for everyone."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message.soft_delete_for_everyone()

        return Response(
            {"detail": "Message deleted for everyone."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=[MESSAGE_TAG],
        summary="Mark message as seen",
        description=(
            "Marks one message as delivered/read/seen for the authenticated user. "
            "The sender cannot mark their own message as seen."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Message marked as seen.",
            ),
            400: OpenApiResponse(
                response=DetailResponseSerializer,
                description="Sender cannot mark own message as seen.",
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Message not found."),
        },
        examples=[
            OpenApiExample(
                name="Success response",
                value={
                    "detail": "Message marked as seen.",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Sender error response",
                value={
                    "detail": "Sender cannot mark own message as seen.",
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="mark-seen")
    def mark_seen(self, request, pk=None):
        message = get_object_or_404(
            Message.objects.filter(
                conversation__participants__user=request.user,
                deleted_at__isnull=True,
            ).distinct(),
            pk=pk,
        )

        if message.sender_id == request.user.id:
            return Response(
                {"detail": "Sender cannot mark own message as seen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_obj, _ = MessageRecipientStatus.objects.get_or_create(
            message=message,
            user=request.user,
        )

        now = timezone.now()

        if not status_obj.delivered_at:
            status_obj.delivered_at = now

        if not status_obj.read_at:
            status_obj.read_at = now

        status_obj.seen_at = now
        status_obj.save(
            update_fields=[
                "delivered_at",
                "read_at",
                "seen_at",
                "updated_at",
            ]
        )

        participant = ConversationParticipant.objects.filter(
            conversation=message.conversation,
            user=request.user,
        ).first()

        if participant:
            participant.last_read_message = message
            participant.last_read_at = now
            participant.save(
                update_fields=[
                    "last_read_message",
                    "last_read_at",
                    "updated_at",
                ]
            )

        return Response(
            {"detail": "Message marked as seen."},
            status=status.HTTP_200_OK,
        )
