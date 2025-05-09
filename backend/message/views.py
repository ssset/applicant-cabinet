import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified
from applications.models import Application
from org.models import Organization
from org.serializers import OrganizationSerializer
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AvailableOrganizationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        if request.user.role != 'applicant':
            raise ValidationError("Only applicants can access this endpoint")

        cache_key = f"chat_organizations_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        applications = Application.objects.filter(applicant=request.user)
        organizations = Organization.objects.filter(
            buildings__building_specialties__applications__in=applications
        ).distinct()

        serializer = OrganizationSerializer(organizations, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(organizations)} organizations for applicant {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class ChatListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        logger.info(f"Fetching chats for user: {request.user.email}, role: {request.user.role}")
        if request.user.role == 'applicant':
            chats = Chat.objects.filter(applicant=request.user)
        elif request.user.role in ['moderator', 'admin_org']:
            if not request.user.organization:
                raise ValidationError("User has no organization assigned")
            chats = Chat.objects.filter(organization=request.user.organization)
        else:
            raise ValidationError("Access denied")

        serializer = ChatSerializer(chats, many=True)
        logger.info(f"Retrieved {len(chats)} chats for {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        logger.info(f"Creating chat for user: {request.user.email}, role: {request.user.role}")
        if request.user.role != 'applicant':
            raise ValidationError("Only applicants can create chats")

        organization_id = request.data.get('organization_id')
        if not organization_id:
            raise ValidationError("Organization ID is required")

        if not Application.objects.filter(
            applicant=request.user,
            building_specialty__building__organization__id=organization_id
        ).exists():
            raise ValidationError("You can only create a chat with an organization you applied to")

        organization = Organization.objects.get(id=organization_id)

        existing_chat = Chat.objects.filter(applicant=request.user, organization=organization).first()
        if existing_chat:
            serializer = ChatSerializer(existing_chat)
            logger.info(f"Chat {existing_chat.id} already exists for {request.user.email}, returning existing chat")
            return Response(serializer.data, status=status.HTTP_200_OK)

        chat = Chat.objects.create(
            applicant=request.user,
            organization=organization
        )
        serializer = ChatSerializer(chat)
        logger.info(f"Chat {chat.id} created by {request.user.email} with organization {organization.name}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ChatDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        logger.info(f"Fetching chat details for user: {request.user.email}, role: {request.user.role}")
        chat_id = request.query_params.get('id')
        if not chat_id:
            raise ValidationError("Chat ID is required")

        chat = Chat.objects.get(id=chat_id)

        if request.user.role == 'applicant':
            if chat.applicant != request.user:
                raise ValidationError("Access denied")
        elif request.user.role in ['moderator', 'admin_org']:
            if not request.user.organization:
                raise ValidationError("User has no organization assigned")
            if chat.organization != request.user.organization:
                raise ValidationError("Access denied")
        else:
            raise ValidationError("Access denied")

        serializer = ChatSerializer(chat)
        logger.info(f"Retrieved chat {chat.id} for {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        logger.info(f"Sending message for user: {request.user.email}, role: {request.user.role}")
        chat_id = request.data.get('chat_id')
        content = request.data.get('content')

        if not chat_id:
            raise ValidationError("Chat ID is required")
        if not content:
            raise ValidationError("Message content is required")

        chat = Chat.objects.get(id=chat_id)

        if request.user.role == 'applicant':
            if chat.applicant != request.user:
                raise ValidationError("Access denied")
        elif request.user.role in ['moderator', 'admin_org']:
            if not request.user.organization:
                raise ValidationError("User has no organization assigned")
            if chat.organization != request.user.organization:
                raise ValidationError("Access denied")
        else:
            raise ValidationError("Access denied")

        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content
        )
        serializer = MessageSerializer(message)
        logger.info(f"Message sent in chat {chat.id} by {request.user.email}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)