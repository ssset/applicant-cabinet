from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant, IsModerator, IsAdminOrg
from org.models import Specialty, BuildingSpecialty, Organization
from org.serializers import SpecialtySerializer, BuildingSpecialtySerializer, OrganizationSerializer
from .models import Application
from users.models import ApplicantProfile
from .serializers import ApplicationSerializer, LeaderboardSerializer
from django.core.cache import cache
from applicant.tasks import send_email_task
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение списка заявок абитуриента",
        description="Возвращает список всех заявок, поданных текущим авторизованным абитуриентом. Каждая заявка включает информацию о специальности, корпусе и организации, к которой относится специальность. Данные дополняются информацией об организации в структуре корпуса.",
        responses={
            200: OpenApiResponse(
                description="Список заявок успешно получен",
                response=ApplicationSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "status": "pending",
                                "priority": 1,
                                "funding_basis": "budget",
                                "created_at": "2025-06-14T12:00:00Z",
                                "building_specialty": {
                                    "id": 1,
                                    "building": {
                                        "id": 1,
                                        "name": "Главный корпус",
                                        "address": "ул. Ленина, 10",
                                        "phone": "+79991234567",
                                        "email": "info@university.ru",
                                        "organization": {
                                            "id": 1,
                                            "name": "Университет",
                                            "email": "contact@university.ru",
                                            "city": "Москва"
                                        }
                                    },
                                    "specialty": {
                                        "id": 1,
                                        "code": "09.03.01",
                                        "name": "Информатика",
                                        "organization": {
                                            "id": 1,
                                            "name": "Университет",
                                            "email": "contact@university.ru",
                                            "city": "Москва"
                                        }
                                    }
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
                description="Недостаточно прав или email не подтверждён",
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
        applications = Application.objects.filter(applicant=request.user)
        serializer = ApplicationSerializer(applications, many=True)

        data = serializer.data

        logger.info(f"Raw serialized data for {request.user.email}: {data}")

        for app in data:
            if 'building_specialty' not in app or not app['building_specialty']:
                logger.warning(f"Application {app['id']} has no building_specialty")
                continue

            building_specialty = app['building_specialty']
            if 'building' not in building_specialty or not building_specialty['building']:
                logger.warning(f"Application {app['id']} has no building in building_specialty")
                continue

            building = building_specialty['building']
            if 'specialty' not in building_specialty or not building_specialty['specialty']:
                logger.warning(f"Application {app['id']} has no specialty in building_specialty")
                continue

            specialty = building_specialty['specialty']
            if 'organization' not in specialty or not specialty['organization']:
                logger.warning(f"Application {app['id']} has no organization in specialty")
                continue

            building['organization'] = specialty['organization']
            logger.info(f"Added organization to building for application {app['id']}")

        logger.info(f"Processed data for {request.user.email}: {data}")
        logger.info(f"Retrieved {len(applications)} applications for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создание новой заявки",
        description="Позволяет авторизованному абитуриенту подать новую заявку на специальность в выбранном корпусе. Требуется заполненный профиль абитуриента. Заявка включает приоритет, тип финансирования и идентификатор BuildingSpecialty.",
        request=ApplicationSerializer,
        responses={
            201: OpenApiResponse(
                description="Заявка успешно создана",
                response=ApplicationSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "status": "pending",
                            "priority": 1,
                            "funding_basis": "budget",
                            "created_at": "2025-06-14T12:00:00Z",
                            "building_specialty": {
                                "id": 1,
                                "building": {
                                    "id": 1,
                                    "name": "Главный корпус",
                                    "address": "ул. Ленина, 10",
                                    "phone": "+79991234567",
                                    "email": "info@university.ru",
                                    "organization": {
                                        "id": 1,
                                        "name": "Университет",
                                        "email": "contact@university.ru",
                                        "city": "Москва"
                                    }
                                },
                                "specialty": {
                                    "id": 1,
                                    "code": "09.03.01",
                                    "name": "Информатика",
                                    "organization": {
                                        "id": 1,
                                        "name": "Университет",
                                        "email": "contact@university.ru",
                                        "city": "Москва"
                                    }
                                }
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или профиль абитуриента не заполнен",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={
                            "message": "Вы должны заполнить профиль абитуриента перед подачей заявления."
                        }
                    ),
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={
                            "building_specialty": ["Это поле обязательно"],
                            "priority": ["Число должно быть от 1 до 3"]
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
                description="Недостаточно прав или email не подтверждён",
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
                    "building_specialty": 1,
                    "priority": 1,
                    "funding_basis": "budget"
                }
            )
        ]
    )
    def post(self, request):
        if not ApplicantProfile.objects.filter(user=request.user).exists():
            logger.warning(f"User {request.user.email} attempted to submit an application without a profile")
            raise ValidationError({"message": "Вы должны заполнить профиль абитуриента перед подачей заявления."})

        serializer = ApplicationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        logger.info(f"Application {application.id} submitted by {request.user.email}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Удаление заявки",
        description="Позволяет авторизованному абитуриенту удалить свою заявку, если она находится в статусе 'pending'. Требуется указать идентификатор заявки в параметре запроса.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор заявки для удаления",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Заявка успешно удалена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Application deleted"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор заявки отсутствует или заявка не в статусе 'pending'",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Application ID is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка статуса",
                        value={"detail": "Cannot delete an application that is already accepted or rejected"}
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
                description="Недостаточно прав или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Заявка не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Application matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request):
        application_id = request.query_params.get('id')
        if not application_id:
            raise ValidationError("Application ID is required")
        application = Application.objects.get(id=application_id, applicant=request.user)
        if application.status != 'pending':
            raise ValidationError("Cannot delete an application that is already accepted or rejected")
        application.delete()
        logger.info(f"Application {application_id} deleted by {request.user.email}")
        return Response({'message': 'Application deleted'}, status=status.HTTP_204_NO_CONTENT)

class AvailableSpecialtiesView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение списка доступных специальностей",
        description="Возвращает список специальностей, доступных для подачи заявки, с возможностью фильтрации по идентификатору организации или городу. Если указан идентификатор специальности, возвращается информация только об одной специальности.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор специальности для получения информации об одной специальности",
                required=False,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            ),
            OpenApiParameter(
                name="organization_id",
                type=int,
                location="query",
                description="Идентификатор организации для фильтрации специальностей",
                required=False,
                examples=[
                    OpenApiExample(name="Пример ID организации", value=1)
                ]
            ),
            OpenApiParameter(
                name="city",
                type=str,
                location="query",
                description="Город для фильтрации специальностей по организациям в этом городе",
                required=False,
                examples=[
                    OpenApiExample(name="Пример города", value="Москва")
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Список специальностей успешно получен",
                response=SpecialtySerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа для списка",
                        value=[
                            {
                                "id": 1,
                                "code": "09.03.01",
                                "name": "Информатика",
                                "organization": {
                                    "id": 1,
                                    "name": "Университет",
                                    "email": "contact@university.ru",
                                    "city": "Москва"
                                }
                            },
                            {
                                "id": 2,
                                "code": "09.03.02",
                                "name": "Программная инженерия",
                                "organization": {
                                    "id": 1,
                                    "name": "Университет",
                                    "email": "contact@university.ru",
                                    "city": "Москва"
                                }
                            }
                        ]
                    ),
                    OpenApiExample(
                        name="Пример ответа для одной специальности",
                        value={
                            "id": 1,
                            "code": "09.03.01",
                            "name": "Информатика",
                            "organization": {
                                "id": 1,
                                "name": "Университет",
                                "email": "contact@university.ru",
                                "city": "Москва"
                            }
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
                description="Недостаточно прав или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Специальность не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Specialty matches the given query."}
                    )
                ]
            )
        }
    )
    def get(self, request):
        specialty_id = request.query_params.get('id')
        organization_id = request.query_params.get('organization_id')
        city = request.query_params.get('city')

        cache_key = f"specialties_{organization_id or 'all'}_{city or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data is not None and not specialty_id:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        specialties = Specialty.objects.all()

        if organization_id:
            specialties = specialties.filter(organization_id=organization_id)

        if city:
            specialties = specialties.filter(organization__city__iexact=city)

        if specialty_id:
            specialty = specialties.get(id=specialty_id)
            serializer = SpecialtySerializer(specialty)
            logger.info(f"Retrieved specialty {specialty_id} for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = SpecialtySerializer(specialties, many=True)
        data = serializer.data
        if not specialty_id:
            cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(specialties)} specialties for {request.user.email} with city {city or 'all'}")
        return Response(data, status=status.HTTP_200_OK)

class AvailableCitiesView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение списка доступных городов",
        description="Возвращает отсортированный список уникальных городов, в которых находятся организации, зарегистрированные в системе.",
        responses={
            200: OpenApiResponse(
                description="Список городов успешно получен",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=["Москва", "Санкт-Петербург", "Казань"]
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
                description="Недостаточно прав или email не подтверждён",
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
        cache_key = "available_cities"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        cities = Organization.objects.values_list('city', flat=True).distinct()
        cities = [city for city in cities if city]
        data = sorted(cities)
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(data)} unique cities for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class ApplicationAttemptsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение количества попыток подачи заявки",
        description="Возвращает количество поданных заявок на указанную специальность в корпусе и количество оставшихся попыток (максимум 3 попытки на одну специальность).",
        parameters=[
            OpenApiParameter(
                name="building_specialty_id",
                type=int,
                location="query",
                description="Идентификатор специальности в корпусе",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Информация о попытках успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "attempts": 2,
                            "remaining": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор специальности в корпусе отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Building specialty ID is required"}
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
                description="Недостаточно прав или email не подтверждён",
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
        building_specialty_id = request.query_params.get('building_specialty_id')
        if not building_specialty_id:
            raise ValidationError("Building specialty ID is required")

        attempts = Application.objects.filter(
            applicant=request.user,
            building_specialty_id=building_specialty_id
        ).count()

        logger.info(f"Retrieved {attempts} application attempts for {request.user.email} on building_specialty {building_specialty_id}")
        return Response({'attempts': attempts, 'remaining': max(0, 3 - attempts)}, status=status.HTTP_200_OK)

class AvailableOrganizationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    @extend_schema(
        summary="Получение списка доступных организаций",
        description="Возвращает список организаций, доступных для подачи заявки, с возможностью фильтрации по городу.",
        parameters=[
            OpenApiParameter(
                name="city",
                type=str,
                location="query",
                description="Город для фильтрации организаций",
                required=False,
                examples=[
                    OpenApiExample(name="Пример города", value="Москва")
                ]
            )
        ],
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
                            },
                            {
                                "id": 2,
                                "name": "Технический институт",
                                "email": "info@tech.ru",
                                "phone": "+79997654321",
                                "address": "пр. Мира, 20",
                                "city": "Москва",
                                "website": "www.tech.ru",
                                "description": "Техническое образование мирового уровня"
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
                description="Недостаточно прав или email не подтверждён",
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
        city = request.query_params.get('city')

        cache_key = f"organizations_{city or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        organizations = Organization.objects.all()

        if city:
            organizations = organizations.filter(city__iexact=city)

        serializer = OrganizationSerializer(organizations, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(organizations)} organizations for {request.user.email} with city {city or 'all'}")
        return Response(data, status=status.HTTP_200_OK)

class ModeratorApplicationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Получение списка заявок для модератора",
        description="Возвращает список заявок, поданных на специальности в корпусах организации, к которой привязан текущий модератор или администратор организации.",
        responses={
            200: OpenApiResponse(
                description="Список заявок успешно получен",
                response=ApplicationSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "status": "pending",
                                "priority": 1,
                                "funding_basis": "budget",
                                "created_at": "2025-06-14T12:00:00Z",
                                "building_specialty": {
                                    "id": 1,
                                    "building": {
                                        "id": 1,
                                        "name": "Главный корпус",
                                        "address": "ул. Ленина, 10",
                                        "phone": "+79991234567",
                                        "email": "info@university.ru"
                                    },
                                    "specialty": {
                                        "id": 1,
                                        "code": "09.03.01",
                                        "name": "Информатика",
                                        "organization": {
                                            "id": 1,
                                            "name": "Университет",
                                            "email": "contact@university.ru",
                                            "city": "Москва"
                                        }
                                    }
                                }
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="У пользователя нет привязанной организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
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
                description="Недостаточно прав или email не подтверждён",
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
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization
        )
        serializer = ApplicationSerializer(applications, many=True)
        logger.info(f"Retrieved {len(applications)} applications for organization {request.user.organization.name}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class ModeratorApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Получение деталей заявки для модератора",
        description="Возвращает информацию о конкретной заявке или позволяет перемещаться между заявками (вперёд/назад) в рамках организации модератора. Если ID не указан, возвращается первая заявка.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор заявки для получения деталей",
                required=False,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            ),
            OpenApiParameter(
                name="direction",
                type=str,
                location="query",
                description="Направление навигации: 'next' для следующей заявки, 'prev' для предыдущей",
                required=False,
                examples=[
                    OpenApiExample(name="Пример направления", value="next")
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Детали заявки успешно получены",
                response=ApplicationSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "status": "pending",
                            "priority": 1,
                            "funding_basis": "budget",
                            "created_at": "2025-06-14T12:00:00Z",
                            "building_specialty": {
                                "id": 1,
                                "building": {
                                    "id": 1,
                                    "name": "Главный корпус",
                                    "address": "ул. Ленина, 10",
                                    "phone": "+79991234567",
                                    "email": "info@university.ru"
                                },
                                "specialty": {
                                    "id": 1,
                                    "code": "09.03.01",
                                    "name": "Информатика",
                                    "organization": {
                                        "id": 1,
                                        "name": "Университет",
                                        "email": "contact@university.ru",
                                        "city": "Москва"
                                    }
                                }
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Неверные параметры или заявки не найдены",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Application ID is required for navigation"}
                    ),
                    OpenApiExample(
                        name="Ошибка отсутствия заявок",
                        value={"detail": "No applications found"}
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
                description="Недостаточно прав или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Заявка не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Application matches the given query."}
                    )
                ]
            )
        }
    )
    def get(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        application_id = request.query_params.get('id')
        direction = request.query_params.get('direction')

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization
        ).order_by('id')

        if not applications.exists():
            raise ValidationError("No applications found")

        if direction:
            if not application_id:
                raise ValidationError("Application ID is required for navigation")
            current_application = applications.get(id=application_id)
            application_ids = list(applications.values_list('id', flat=True))
            current_index = application_ids.index(int(application_id))

            if direction == 'next':
                next_index = current_index + 1 if current_index + 1 < len(application_ids) else 0
                application = applications[next_index]
            elif direction == 'prev':
                prev_index = current_index - 1 if current_index - 1 >= 0 else len(application_ids) - 1
                application = applications[prev_index]
            else:
                raise ValidationError("Direction must be 'next' or 'prev'")
        else:
            if not application_id:
                application = applications.first()
            else:
                application = applications.get(id=application_id)

        serializer = ApplicationSerializer(application)
        logger.info(f"Retrieved application {application.id} for {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Обновление статуса заявки модератором",
        description="Позволяет модератору или администратору организации принять или отклонить заявку. При отклонении требуется указать причину. После изменения статуса абитуриенту отправляется email-уведомление.",
        request={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Идентификатор заявки"},
                "action": {"type": "string", "enum": ["accept", "reject"], "description": "Действие: принять или отклонить"},
                "reject_reason": {"type": "string", "description": "Причина отклонения (обязательна при action='reject')"}
            },
            "required": ["id", "action"]
        },
        responses={
            200: OpenApiResponse(
                description="Статус заявки успешно обновлён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Application accepted"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Неверные параметры или заявка не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Reject reason is required when rejecting an application"}
                    ),
                    OpenApiExample(
                        name="Ошибка действия",
                        value={"detail": "Action must be 'accept' or 'reject'"}
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
                description="Недостаточно прав или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Заявка не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Application matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса для принятия",
                value={
                    "id": 1,
                    "action": "accept"
                }
            ),
            OpenApiExample(
                name="Пример запроса для отклонения",
                value={
                    "id": 1,
                    "action": "reject",
                    "reject_reason": "Недостаточный средний балл"
                }
            )
        ]
    )
    def patch(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        application_id = request.data.get('id')
        action = request.data.get('action')
        reject_reason = request.data.get('reject_reason')

        if not application_id:
            raise ValidationError("Application ID is required")
        if not action:
            raise ValidationError("Action is required")
        if action == 'reject' and not reject_reason:
            raise ValidationError("Reject reason is required when rejecting an application")

        application = Application.objects.get(
            id=application_id,
            building_specialty__building__organization=request.user.organization
        )

        if action == 'accept':
            application.status = 'accepted'
            application.reject_reason = None
        elif action == 'reject':
            application.status = 'rejected'
            application.reject_reason = reject_reason
        else:
            raise ValidationError("Action must be 'accept' or 'reject'")

        application.save()

        subject = f"Application {application.id} Status Update"
        message = f"Your application has been {application.status}."
        if reject_reason:
            message += f" Reason: {reject_reason}"
        send_email_task.delay(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email]
        )
        logger.info(f"Email notification task queued for application {application.id}")

        logger.info(f"Application {application.id} {action}ed by {request.user.email} with reason: {reject_reason}")
        return Response({'message': f'Application {action}ed'}, status=status.HTTP_200_OK)

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant | IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Получение рейтингового списка",
        description="Возвращает рейтинговый список заявок на указанную специальность в корпусе для бюджетных мест, отсортированный по среднему баллу, приоритету и дате подачи. Включает информацию о специальности, заявках и ранге текущего пользователя (если он абитуриент).",
        parameters=[
            OpenApiParameter(
                name="building_specialty_id",
                type=int,
                location="query",
                description="Идентификатор специальности в корпусе",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Рейтинговый список успешно получен",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "building_specialty": {
                                "id": 1,
                                "building": {
                                    "id": 1,
                                    "name": "Главный корпус",
                                    "address": "ул. Ленина, 10",
                                    "phone": "+79991234567",
                                    "email": "info@university.ru"
                                },
                                "specialty": {
                                    "id": 1,
                                    "code": "09.03.01",
                                    "name": "Информатика",
                                    "organization": {
                                        "id": 1,
                                        "name": "Университет",
                                        "email": "contact@university.ru",
                                        "city": "Москва"
                                    }
                                }
                            },
                            "leaderboard": [
                                {
                                    "id": 1,
                                    "applicant": {
                                        "email": "student@university.ru",
                                        "applicant_profile": {
                                            "average_grade": 4.8
                                        }
                                    },
                                    "status": "pending",
                                    "priority": 1,
                                    "funding_basis": "budget",
                                    "created_at": "2025-06-14T12:00:00Z",
                                    "rank": 1
                                }
                            ],
                            "user_rank": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор специальности в корпусе отсутствует или нет прав доступа",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Building specialty ID is required"}
                    ),
                    OpenApiExample(
                        name="Ошибка доступа",
                        value={"detail": "You do not have permission to view this leaderboard"}
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
                description="Недостаточно прав или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Специальность в корпусе не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No BuildingSpecialty matches the given query."}
                    )
                ]
            )
        }
    )
    def get(self, request):
        building_specialty_id = request.query_params.get('building_specialty_id')
        if not building_specialty_id:
            raise ValidationError("Building specialty ID is required")

        cache_key = f"leaderboard_{building_specialty_id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id)

        logger.info(f"User {request.user.email} role: {request.user.role}, organization: {getattr(request.user, 'organization', 'None')}")
        if request.user.role == 'admin_org' and not getattr(request.user, 'organization', None):
            logger.warning(f"Admin_org {request.user.email} has no organization assigned")

        if request.user.role == 'admin_org' and request.user.organization:
            if building_specialty.building.organization != request.user.organization:
                raise ValidationError("You do not have permission to view this leaderboard")

        applications = Application.objects.filter(
            building_specialty=building_specialty,
            funding_basis='budget'
        ).select_related('applicant__applicant_profile').order_by(
            '-applicant__applicant_profile__average_grade', 'priority', 'created_at'
        )

        ranked_applications = []
        for rank, application in enumerate(applications, start=1):
            application.rank = rank
            ranked_applications.append(application)

        serializer = LeaderboardSerializer(ranked_applications, many=True)
        data = {
            'building_specialty': BuildingSpecialtySerializer(building_specialty).data,
            'leaderboard': serializer.data,
            'user_rank': self.get_user_rank(request.user, ranked_applications)
        }
        cache.set(cache_key, data, timeout=300)
        logger.info(f"Retrieved leaderboard for BuildingSpecialty {building_specialty_id}")
        return Response(data, status=status.HTTP_200_OK)

    def get_user_rank(self, user, ranked_applications):
        for application in ranked_applications:
            if application.applicant == user:
                return application.rank
        return None