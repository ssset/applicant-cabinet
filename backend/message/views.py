from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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
import logging

logger = logging.getLogger(__name__)

class AvailableOrganizationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @extend_schema(
        summary="Получение списка организаций для чата",
        description="Возвращает список организаций, в которые абитуриент подавал заявки. Доступно только для пользователей с ролью 'applicant'. Данные кэшируются на 1 час.",
        responses={
            200: OpenApiResponse(
                description="Список организаций успешно получен",
                response=OrganizationSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "name": "Университет",
                                "email": "contact@university.ru",
                                "phone": "+79991234567",
                                "address": "ул. Ленина, 10",
                                "city": "Москва",
                                "website": "www.university.ru",
                                "description": "Ведущий вуз страны"
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно прав для доступа",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Only applicants can access this endpoint"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
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

    @extend_schema(
        summary="Получение списка чатов",
        description="Возвращает список чатов, в которых участвует пользователь. Для абитуриентов — чаты, созданные ими. Для модераторов или администраторов организаций — чаты, связанные с их организацией.",
        responses={
            200: OpenApiResponse(
                description="Список чатов успешно получен",
                response=ChatSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "applicant": {
                                    "id": 1,
                                    "email": "user@example.com"
                                },
                                "organization": {
                                    "id": 1,
                                    "name": "Университет"
                                },
                                "created_at": "2025-06-14T12:00:00Z"
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно прав или пользователь не привязан к организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "User has no organization assigned"}
                    ),
                    OpenApiExample(
                        name="Ошибка доступа",
                        value={"detail": "Access denied"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
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

    @extend_schema(
        summary="Создание нового чата",
        description="Позволяет абитуриенту создать чат с организацией, в которую он подавал заявку. Если чат уже существует, возвращается информация о нём.",
        request={
            "type": "object",
            "properties": {
                "organization_id": {"type": "integer", "description": "Идентификатор организации"}
            },
            "required": ["organization_id"]
        },
        responses={
            201: OpenApiResponse(
                description="Чат успешно создан",
                response=ChatSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "applicant": {
                                "id": 1,
                                "email": "user@example.com"
                            },
                            "organization": {
                                "id": 1,
                                "name": "Университет"
                            },
                            "created_at": "2025-06-14T12:00:00Z"
                        }
                    )
                ]
            ),
            200: OpenApiResponse(
                description="Чат уже существует",
                response=ChatSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "applicant": {
                                "id": 1,
                                "email": "user@example.com"
                            },
                            "organization": {
                                "id": 1,
                                "name": "Университет"
                            },
                            "created_at": "2025-06-14T12:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Неверные данные или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Organization ID is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка доступа",
                        value={"detail": "Only applicants can create chats"}
                    ),
                    OpenApiExample(
                        name="Ошибка заявки",
                        value={"detail": "You can only create a chat with an organization you applied to"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Организация не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Organization matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "organization_id": 1
                }
            )
        ]
    )
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

    @extend_schema(
        summary="Получение деталей чата",
        description="Возвращает информацию о чате по его идентификатору. Доступно для абитуриента, создавшего чат, или модераторов/администраторов организации, связанной с чатом.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор чата",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Детали чата успешно получены",
                response=ChatSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "applicant": {
                                "id": 1,
                                "email": "user@example.com"
                            },
                            "organization": {
                                "id": 1,
                                "name": "Университет"
                            },
                            "created_at": "2025-06-14T12:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Неверные параметры или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Chat ID is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка доступа",
                        value={"detail": "Access denied"}
                    ),
                    OpenApiExample(
                        name="Ошибка организации",
                        value={"detail": "User has no organization assigned"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Чат не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Chat matches the given query."}
                    )
                ]
            )
        }
    )
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

    @extend_schema(
        summary="Отправка сообщения в чат",
        description="Позволяет отправить сообщение в указанный чат. Доступно для абитуриента, создавшего чат, или модераторов/администраторов организации, связанной с чатом.",
        request={
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Идентификатор чата"},
                "content": {"type": "string", "description": "Содержимое сообщения"}
            },
            "required": ["chat_id", "content"]
        },
        responses={
            201: OpenApiResponse(
                description="Сообщение успешно отправлено",
                response=MessageSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "chat": 1,
                            "sender": {
                                "id": 1,
                                "email": "user@example.com"
                            },
                            "content": "Здравствуйте, есть вопросы по поступлению",
                            "created_at": "2025-06-14T12:00:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Неверные параметры или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Chat ID is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка содержимого",
                        value={"detail": "Message content is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка доступа",
                        value={"detail": "Access denied"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Чат не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Chat matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "chat_id": 1,
                    "content": "Здравствуйте, есть вопросы по поступлению"
                }
            )
        ]
    )
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