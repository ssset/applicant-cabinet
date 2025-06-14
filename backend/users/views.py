from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from .serializers import ApplicantProfileSerializer, CustomUserSerializer, AdminOrgListSerializer
from auth_app.serializers import RegisterSerializer
from .models import CustomUser, ApplicantProfile
from auth_app.permissions import IsApplicant, IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
from org.models import Organization
from applicant.tasks import process_attestation_image_task
from django.core.cache import cache
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)

class ApplicantProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение профиля абитуриента",
        description="Возвращает данные профиля абитуриента для текущего пользователя. Доступно только для пользователей с ролью 'applicant' и подтверждённым email.",
        responses={
            200: OpenApiResponse(
                response=ApplicantProfileSerializer,
                description="Профиль успешно получен",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "user": 1,
                            "name": "Иван Иванов",
                            "date_of_birth": "2000-05-15",
                            "email": "ivan@example.com",
                            "phone": "+998901234567",
                            "attestation_photo": "/media/attestation/photo.jpg",
                            "calculated_average_grade": 4.5
                        }
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"message": "Профиль абитуриента еще не создан"},
                    )
                    ]
            )
        }
    )
    def get(self, request):
        logger.debug(f"GET /api/users/profile/ for user {request.user.id}")
        profile = ApplicantProfile.objects.filter(user=request.user).first()
        if not profile:
            logger.info(f"No profile found for user {request.user.id}")
            return Response(
                {"message": "Профиль абитуриента еще не создан"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ApplicantProfileSerializer(profile)
        logger.debug(f"Returning profile data for user {request.user.id}: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создание профиля абитуриента",
        description="Создаёт профиль абитуриента для текущего пользователя. Если предоставлено фото аттестата, запускается задача обработки изображения. Доступно только для пользователей с ролью 'applicant' и подтверждённым email.",
        request=ApplicantProfileSerializer,
        responses={
            201: OpenApiResponse(
                response=ApplicantProfileSerializer,
                description="Профиль успешно создан",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "user": 1,
                            "name": "Иван Иванов",
                            "date_of_birth": "2000-05-15",
                            "email": "ivan@example.com",
                            "phone": "+998901234567",
                            "attestation_photo": "/media/attestation/photo.jpg",
                            "calculated_average_grade": 0.0
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или профиль уже существует",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "Profile already exists"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "name": "Иван Иванов",
                    "date_of_birth": "2000-05-15",
                    "email": "ivan@example.com",
                    "phone": "+998901234567"
                }
            )
        ]
    )
    def post(self, request):
        logger.debug(f"POST /api/users/profile/ for user {request.user.id}, data={request.data}")
        if ApplicantProfile.objects.filter(user=request.user).exists():
            logger.error(f"Profile already exists for user {request.user.id}")
            raise ValidationError("Profile already exists")

        serializer = ApplicantProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(user=request.user)

        if 'attestation_photo' in request.FILES:
            logger.info(
                f"New attestation photo uploaded for user {request.user.id} "
                f"(profile {profile.id}), path: {profile.attestation_photo.path}"
            )
            task = process_attestation_image_task.delay(profile.id, profile.attestation_photo.path)
            logger.info(f"Task {task.id} started for processing attestation photo for user {request.user.id}")
            profile.task_id = task.id
            profile.save()
        else:
            logger.info(f"No attestation photo in request for user {request.user.id}")

        logger.debug(f"Created profile for user {request.user.id}: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Обновление профиля абитуриента",
        description="Частично обновляет профиль абитуриента для текущего пользователя. Если предоставлено новое фото аттестата, запускается задача обработки изображения. Доступно только для пользователей с ролью 'applicant' и подтверждённым email.",
        request=ApplicantProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=ApplicantProfileSerializer,
                description="Профиль успешно обновлён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "user": 1,
                            "name": "Иван Иванов Петров",
                            "date_of_birth": "2000-05-15",
                            "email": "ivan@example.com",
                            "phone": "+998901234567",
                            "attestation_photo": "/media/attestation/new_photo.jpg",
                            "calculated_average_grade": 4.5
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"email": ["Некорректный формат email"]}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No ApplicantProfile matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "name": "Иван Иванов Петров",
                    "phone": "+998901234567"
                }
            )
        ]
    )
    def patch(self, request):
        logger.debug(f"PATCH /api/users/profile/ for user {request.user.id}, data={request.data}")
        profile = ApplicantProfile.objects.get(user=request.user)
        serializer = ApplicantProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        if 'attestation_photo' in request.FILES:
            logger.info(f"Attestation photo updated via PATCH for user {request.user.id} (profile {profile.id})")
            task = process_attestation_image_task.delay(profile.id, profile.attestation_photo.path)
            profile.task_id = str(task.id)
            profile.save()

        logger.debug(f"Updated profile for user {request.user.id}: {serializer.data}")
        return Response(ApplicantProfileSerializer(profile).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление профиля абитуриента",
        description="Удаляет профиль абитуриента текущего пользователя. Доступно только для пользователей с ролью 'applicant' и подтверждённым email.",
        responses={
            204: OpenApiResponse(
                description="Профиль успешно удалён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Profile deleted"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No ApplicantProfile matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request):
        logger.debug(f"DELETE /api/users/profile/ for user {request.user.id}")
        profile = ApplicantProfile.objects.get(user=request.user)
        profile.delete()
        logger.info(f"Profile deleted for user {request.user.id}")
        return Response({'message': 'Profile deleted'}, status=status.HTTP_204_NO_CONTENT)

class AdminAppCreationView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Создание администратора системы",
        description="Создаёт первого администратора системы (admin_app). Доступно без аутентификации, но только если администратор ещё не существует.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Администратор успешно создан",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Admin app registered, check your email for verification code"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или администратор уже существует",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "Admin app already exists"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "admin@app.example.com",
                    "password": "securepassword123",
                    "password2": "securepassword123"
                }
            )
        ]
    )
    def post(self, request):
        if CustomUser.objects.filter(role='admin_app').exists():
            raise ValidationError("Admin app already exists")

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'admin_app'
        user.save()
        return Response({
            'message': 'Admin app registered, check your email for verification code'
        }, status=status.HTTP_201_CREATED)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получение данных текущего пользователя",
        description="Возвращает данные текущего пользователя. Данные кэшируются на 1 час. Доступно для всех аутентифицированных пользователей.",
        responses={
            200: OpenApiResponse(
                response=CustomUserSerializer,
                description="Данные пользователя успешно получены",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "email": "user@example.com",
                            "role": "applicant",
                            "organization": None
                        }
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
            )
        }
    )
    def get(self, request):
        cache_key = f"current_user_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        serializer = CustomUserSerializer(request.user)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Обновление данных текущего пользователя",
        description="Частично обновляет данные текущего пользователя. Кэш очищается после обновления. Доступно для всех аутентифицированных пользователей.",
        request=CustomUserSerializer,
        responses={
            200: OpenApiResponse(
                response=CustomUserSerializer,
                description="Данные пользователя успешно обновлены",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "email": "newemail@example.com",
                            "role": "applicant",
                            "organization": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"email": ["Некорректный формат"]}
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
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "newemail@example.com"
                }
            )
        ]
    )
    def patch(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(f"current_user_{request.user.id}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminOrgView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    @extend_schema(
        summary="Создание администратора организации",
        description="Создаёт нового администратора организации (admin_org) с привязкой к указанной организации. Доступно только для администраторов системы.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Администратор организации создан",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Admin org registered, check your email for verification code"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или организация не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"organization_id": ["Это поле обязательно"]}
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
                description="Email не подтверждён или недостаточно прав",
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
                    "email": "adminorg@example.com",
                    "password": "securepassword123",
                    "password2": "securepassword123",
                    "organization_id": 1
                }
            )
        ]
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'admin_org'
        organization_id = request.data.get('organization_id')
        organization = Organization.objects.get(id=organization_id)
        user.organization = organization
        user.save()
        return Response({
            'message': 'Admin org registered, check your email for verification code'
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Получение списка администраторов организаций",
        description="Возвращает список всех администраторов организаций (admin_org). Доступно только для администраторов системы.",
        responses={
            200: OpenApiResponse(
                response=AdminOrgListSerializer(many=True),
                description="Список администраторов успешно получен",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "email": "adminorg1@example.com",
                                "organization": {
                                    "id": 1,
                                    "name": "Университет А"
                                }
                            },
                            {
                                "id": 2,
                                "email": "adminorg2@example.com",
                                "organization": {
                                    "id": 2,
                                    "name": "Университет Б"
                                }
                            }
                        ]
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
                description="Email не подтверждён или недостаточно прав",
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
        logger.info("Fetching admin_org users")
        admin_orgs = CustomUser.objects.filter(role='admin_org')
        serializer = AdminOrgListSerializer(admin_orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Обновление администратора организации",
        description="Частично обновляет данные администратора организации по его ID, включая возможность изменения привязки к организации. Доступно только для администраторов системы.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="path",
                description="Идентификатор администратора организации",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=RegisterSerializer,
                description="Администратор организации успешно обновлён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "email": "newadminorg@example.com"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или ID не указан",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "User ID is required"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Администратор или организация не найдены",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No CustomUser matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "newadminorg@example.com",
                    "organization_id": 2
                }
            )
        ]
    )
    def patch(self, request, id=None):
        logger.info(f"AdminOrgView PATCH: user={request.user}, id={id}, data={request.data}")
        if id is None:
            raise ValidationError("User ID is required")

        admin_org = CustomUser.objects.get(id=id, role='admin_org')
        serializer = RegisterSerializer(admin_org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        organization_id = request.data.get('organization_id')
        if organization_id:
            organization = Organization.objects.get(id=organization_id)
            admin_org.organization = organization
            admin_org.save()
        serializer.save()
        logger.info(f"Admin org with id {id} updated by {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление администратора организации",
        description="Удаляет администратора организации по его ID. Доступно только для администраторов системы.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="path",
                description="Идентификатор администратора организации",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Администратор организации успешно удалён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Admin org deleted"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="ID не указан",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "User ID is required"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Администратор не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No CustomUser matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request, id=None):
        if id is None:
            raise ValidationError("User ID is required")

        admin_org = CustomUser.objects.get(id=id, role='admin_org')
        admin_org.delete()
        logger.info(f"Admin org with id {id} deleted by {request.user.email}")
        return Response({'message': 'Admin org deleted'}, status=status.HTTP_204_NO_CONTENT)

class ModeratorView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    @extend_schema(
        summary="Создание модератора",
        description="Создаёт нового модератора с привязкой к организации текущего пользователя. Доступно только для администраторов организации.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Модератор успешно создан",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Moderator registered, check email for verification code"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"email": ["Это поле обязательно"]}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "moderator@example.com",
                    "password": "securepassword123",
                    "password2": "securepassword123"
                }
            )
        ]
    )
    def post(self, request):
        logger.info(f'Creating moderator with data: {request.data}')
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'moderator'
        user.organization = request.user.organization
        user.save()
        return Response({
            'message': 'Moderator registered, check email for verification code'
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Получение списка модераторов",
        description="Возвращает список модераторов, привязанных к организации текущего пользователя. Доступно только для администраторов организации.",
        responses={
            200: OpenApiResponse(
                response=RegisterSerializer(many=True),
                description="Список модераторов успешно получен",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "email": "moderator1@example.com"
                            },
                            {
                                "id": 2,
                                "email": "moderator2@example.com"
                            }
                        ]
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
                description="Email не подтверждён или недостаточно прав",
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
        logger.info(f"Fetching moderators for organization: {request.user.organization}")
        moderators = CustomUser.objects.filter(role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderators, many=True)
        logger.info(f"moderators info: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Обновление модератора",
        description="Частично обновляет данные модератора по его ID. Доступно только для администраторов организации, если модератор привязан к их организации.",
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=RegisterSerializer,
                description="Модератор успешно обновлён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "email": "newmoderator@example.com"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или ID не указан",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "User ID is required"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Модератор не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No CustomUser matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "id": 1,
                    "email": "newmoderator@example.com"
                }
            )
        ]
    )
    def patch(self, request):
        logger.info(
            f"ModeratorView PATCH: user={request.user}, authenticated={request.user.is_authenticated}, organization={request.user.organization}")
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        user_id = request.data.get('id')
        if not user_id:
            raise ValidationError("User ID is required")

        moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderator, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление модератора",
        description="Удаляет модератора по его ID, если он привязан к организации текущего пользователя. Доступно только для администраторов организации.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор модератора",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Модератор успешно удалён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Moderator deleted"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="ID не указан",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"detail": "User ID is required"}
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
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Модератор не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No CustomUser matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request):
        user_id = request.query_params.get('id')
        if not user_id:
            raise ValidationError("User ID is required")

        moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
        moderator.delete()
        return Response({'message': 'Moderator deleted'}, status=status.HTTP_204_NO_CONTENT)

class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверка статуса задачи",
        description="Возвращает статус выполнения задачи (например, обработки фото аттестата) по её ID. Если задача завершена успешно, обновляет средний балл в профиле абитуриента. Доступно для всех аутентифицированных пользователей.",
        parameters=[
            OpenApiParameter(
                name="task_id",
                type=str,
                location="query",
                description="Идентификатор задачи",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value="123e4567-e89b-12d3-a456-426614174000")
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Статус задачи успешно получен",
                examples=[
                    OpenApiExample(
                        name="Задача в ожидании",
                        value={"status": "pending"}
                    ),
                    OpenApiExample(
                        name="Задача завершена",
                        value={"status": "completed", "result": 4.5}
                    ),
                    OpenApiExample(
                        name="Задача не выполнена",
                        value={"status": "failed", "error": "Ошибка обработки изображения"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="ID задачи не указан",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"error": "Task ID is required"}
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
            )
        }
    )
    def get(self, request):
        task_id = request.query_params.get('task_id')
        logger.debug(f"GET /api/task-status/?task_id={task_id} for user {request.user.id}")
        if not task_id:
            logger.error("Task ID is required")
            return Response({"error": "Task ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(task_id)
        logger.debug(f"Task {task_id} state: {task.state}")
        if task.state == 'PENDING':
            response = {'status': 'pending'}
        elif task.state == 'SUCCESS':
            result = task.result
            logger.debug(f"Task {task_id} result: {result}")
            if isinstance(result, dict) and "error" in result:
                response = {'status': 'failed', 'error': result["error"]}
            else:
                response = {'status': 'completed', 'result': result}
                if task.name == 'applicant.tasks.process_attestation_image_task':
                    try:
                        profile = request.user.applicantprofile
                        profile.calculated_average_grade = result
                        profile.task_id = None
                        profile.save()
                        logger.info(f"Updated profile for user {request.user.id} with average grade {result}")
                    except Exception as e:
                        logger.error(f"Failed to update profile for user {request.user.id}: {str(e)}", exc_info=True)
        else:
            response = {'status': 'failed', 'error': str(task.result)}
            logger.error(f"Task {task_id} failed: {str(task.result)}")

        logger.info(f"Task {task_id} status checked: {response}")
        return Response(response, status=status.HTTP_200_OK)