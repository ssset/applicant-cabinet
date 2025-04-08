import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant, IsModerator
from applications.models import Application
from org.models import Organization
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer

logger = logging.getLogger(__name__)


class ChatListView(APIView):
    """
    API для получения списка чатов.
        - Для абитуриентов: чаты с организациями, в которые поданы заявки.
        - Для модераторов: чаты с абитуриентами их организации.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        try:
            if request.user.role == 'applicant':
                # Для абитуриентов: показываем чаты с организациями, в которые поданы заявки
                applications = Application.objects.filter(applicant=request.user)
                organizations = Organization.objects.filter(
                    building__building_specialties__applications__in=applications
                ).distinct()
                chats = Chat.objects.filter(applicant=request.user, organization__in=organizations)
            elif request.user.role == 'moderator':
                # Для модераторов: показываем чаты с абитуриентами их организации
                if not request.user.organization:
                    logger.error(f"User {request.user.email} has no organization assigned")
                    return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
                chats = Chat.objects.filter(organization=request.user.organization)
            else:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ChatSerializer(chats, many=True)
            logger.info(f"Retrieved {len(chats)} chats for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving chats for {request.user.email}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Создание чата (только для абитуриентов).
        Ожидаемые данные:
        - organization_id: ID организации.
        """
        try:
            if request.user.role != 'applicant':
                return Response({'error': 'Only applicants can create chats'}, status=status.HTTP_403_FORBIDDEN)

            organization_id = request.data.get('organization_id')
            if not organization_id:
                raise ValidationError("Organization ID is required")

            # Проверяем, подавал ли абитуриент заявку в эту организацию
            if not Application.objects.filter(
                applicant=request.user,
                building_specialty__building__organization__id=organization_id
            ).exists():
                raise ValidationError("You can only create a chat with an organization you applied to")

            # Проверяем, не существует ли уже чат
            if Chat.objects.filter(applicant=request.user, organization__id=organization_id).exists():
                raise ValidationError("Chat with this organization already exists")

            chat = Chat.objects.create(
                applicant=request.user,
                organization_id=organization_id
            )
            serializer = ChatSerializer(chat)
            logger.info(f"Chat {chat.id} created by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in ChatListView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ChatListView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatDetailView(APIView):
    """
    API для работы с конкретным чатом и отправки сообщений.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        """
        Получение данных чата по ID.
        """
        try:
            chat_id = request.query_params.get('id')
            if not chat_id:
                raise ValidationError("Chat ID is required")

            chat = Chat.objects.get(id=chat_id)

            # Проверяем доступ
            if request.user.role == 'applicant':
                if chat.applicant != request.user:
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'moderator':
                if chat.organization != request.user.organization:
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
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
        """
        Отправка сообщения в чат.
        Ожидаемые данные:
        - chat_id: ID чата.
        - content: Содержание сообщения.
        """
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
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'moderator':
                if chat.organization != request.user.organization:
                    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

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