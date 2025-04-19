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

logger = logging.getLogger(__name__)

class AvailableOrganizationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        if request.user.role != 'applicant':
            logger.warning(f"Access denied for user {request.user.email} with role {request.user.role}")
            return Response({'error': 'Only applicants can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)

        # Получаем организации, в которые абитуриент подавал заявки
        applications = Application.objects.filter(applicant=request.user)
        organizations = Organization.objects.filter(
            buildings__building_specialties__applications__in=applications
        ).distinct()

        serializer = OrganizationSerializer(organizations, many=True)
        logger.info(f"Retrieved {len(organizations)} organizations for applicant {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        logger.info(f"Fetching chats for user: {request.user.email}, role: {request.user.role}")
        try:
            if request.user.role == 'applicant':
                # Для абитуриента: только чаты, которые он создал
                chats = Chat.objects.filter(applicant=request.user)
            elif request.user.role in ['moderator', 'admin_org']:
                # Для модераторов и админов: чаты их организации
                if not request.user.organization:
                    logger.error(f"User {request.user.email} has no organization assigned")
                    return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
                chats = Chat.objects.filter(organization=request.user.organization)
            else:
                logger.error(f"Access denied for user {request.user.email} with role {request.user.role}")
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ChatSerializer(chats, many=True)
            logger.info(f"Retrieved {len(chats)} chats for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving chats for {request.user.email}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        logger.info(f"Creating chat for user: {request.user.email}, role: {request.user.role}")
        try:
            if request.user.role != 'applicant':
                logger.warning(f"Access denied for user {request.user.email} with role {request.user.role}")
                return Response({'error': 'Only applicants can create chats'}, status=status.HTTP_403_FORBIDDEN)

            organization_id = request.data.get('organization_id')
            if not organization_id:
                raise ValidationError("Organization ID is required")

            # Проверяем, подавал ли абитуриент заявку в эту организацию
            if not Application.objects.filter(
                applicant=request.user,
                building_specialty__building__organization__id=organization_id
            ).exists():
                logger.warning(f"User {request.user.email} has not applied to organization {organization_id}")
                raise ValidationError("You can only create a chat with an organization you applied to")

            # Проверяем, существует ли организация
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                logger.warning(f"Organization {organization_id} not found")
                return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

            # Проверяем, не существует ли уже чат
            existing_chat = Chat.objects.filter(applicant=request.user, organization=organization).first()
            if existing_chat:
                serializer = ChatSerializer(existing_chat)
                logger.info(f"Chat {existing_chat.id} already exists for {request.user.email}, returning existing chat")
                return Response(serializer.data, status=status.HTTP_200_OK)

            # Создаём новый чат
            chat = Chat.objects.create(
                applicant=request.user,
                organization=organization
            )
            serializer = ChatSerializer(chat)
            logger.info(f"Chat {chat.id} created by {request.user.email} with organization {organization.name}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in ChatListView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ChatListView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        logger.info(f"Fetching chat details for user: {request.user.email}, role: {request.user.role}")
        try:
            chat_id = request.query_params.get('id')
            if not chat_id:
                raise ValidationError("Chat ID is required")

            chat = Chat.objects.get(id=chat_id)

            # Проверяем доступ
            if request.user.role == 'applicant':
                if chat.applicant != request.user:
                    logger.warning(f"Access denied for applicant {request.user.email} to chat {chat_id}")
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role in ['moderator', 'admin_org']:
                if not request.user.organization:
                    logger.error(f"User {request.user.email} has no organization assigned")
                    return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
                if chat.organization != request.user.organization:
                    logger.warning(f"Access denied for {request.user.role} {request.user.email} to chat {chat_id}")
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                logger.error(f"Access denied for user {request.user.email} with role {request.user.role}")
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ChatSerializer(chat)
            logger.info(f"Retrieved chat {chat.id} for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Chat.DoesNotExist:
            logger.warning(f"Chat {chat_id} not found")
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in ChatDetailView GET: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ChatDetailView GET: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        logger.info(f"Sending message for user: {request.user.email}, role: {request.user.role}")
        try:
            chat_id = request.data.get('chat_id')
            content = request.data.get('content')

            if not chat_id:
                raise ValidationError("Chat ID is required")
            if not content:
                raise ValidationError("Message content is required")

            chat = Chat.objects.get(id=chat_id)

            # Проверяем доступ
            if request.user.role == 'applicant':
                if chat.applicant != request.user:
                    logger.warning(f"Access denied for applicant {request.user.email} to chat {chat_id}")
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role in ['moderator', 'admin_org']:
                if not request.user.organization:
                    logger.error(f"User {request.user.email} has no organization assigned")
                    return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
                if chat.organization != request.user.organization:
                    logger.warning(f"Access denied for {request.user.role} {request.user.email} to chat {chat_id}")
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                logger.error(f"Access denied for user {request.user.email} with role {request.user.role}")
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # Создаём сообщение
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                content=content
            )
            serializer = MessageSerializer(message)
            logger.info(f"Message sent in chat {chat.id} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Chat.DoesNotExist:
            logger.warning(f"Chat {chat_id} not found")
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in ChatDetailView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ChatDetailView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)