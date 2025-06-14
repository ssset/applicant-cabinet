from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .serializers import OrganizationSerializer, BuildingSerializer, SpecialtySerializer, BuildingSpecialtySerializer
from auth_app.permissions import IsEmailVerified, IsAdminApp, IsAdminOrg, IsModerator
from rest_framework.permissions import IsAuthenticated
from .models import Organization, Building, Specialty, BuildingSpecialty
from django.conf import settings
from applicant.tasks import send_email_task
from django.core.cache import cache
from users.models import CustomUser
from yookassa import Configuration, Payment
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from yookassa.domain.notification import WebhookNotification
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

Configuration.account_id = settings.YUKASSA_SHOP_ID
Configuration.secret_key = settings.YUKASSA_SECRET_KEY

class PaymentWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Обработка вебхука ЮKassa",
        description="Обрабатывает уведомления от ЮKassa о статусе платежа. При успешной оплате создаёт организацию и корпус, отправляет уведомления администраторам.",
        request={
            "type": "object",
            "properties": {
                "event": {"type": "string", "description": "Событие вебхука (например, payment.succeeded)"},
                "object": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Идентификатор платежа"},
                        "amount": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string", "description": "Сумма платежа"},
                                "currency": {"type": "string", "description": "Валюта платежа"}
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "institution_name": {"type": "string", "description": "Название организации"},
                                "email": {"type": "string", "description": "Email организации"},
                                "phone": {"type": "string", "description": "Телефон организации"},
                                "address": {"type": "string", "description": "Адрес организации"},
                                "city": {"type": "string", "description": "Город организации"},
                                "website": {"type": "string", "description": "Веб-сайт организации"},
                                "description": {"type": "string", "description": "Описание организации"}
                            }
                        }
                    }
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Вебхук успешно обработан",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Ошибка обработки вебхука или некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"error": "Invalid webhook data"}
                    ),
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"errors": {"name": ["Это поле обязательно"]}}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "event": "payment.succeeded",
                    "object": {
                        "id": "123456789",
                        "amount": {
                            "value": "4000.00",
                            "currency": "RUB"
                        },
                        "metadata": {
                            "institution_name": "Университет",
                            "email": "contact@university.ru",
                            "phone": "+79991234567",
                            "address": "ул. Ленина, 10",
                            "city": "Москва",
                            "website": "www.university.ru",
                            "description": "Ведущий вуз"
                        }
                    }
                }
            )
        ]
    )
    @method_decorator(csrf_exempt)
    def post(self, request):
        logger.debug(f"Получен вебхук: {request.data}")
        try:
            notification = WebhookNotification(request.data)
            logger.info(f"Обработка вебхука: event={notification.event}, payment_id={notification.object.id}")
            if notification.event == 'payment.succeeded':
                payment = notification.object
                metadata = payment.metadata
                logger.debug(f"Метаданные платежа: {metadata}")

                organization_data = {
                    'name': metadata.get('institution_name', 'Не указано'),
                    'email': metadata.get('email', 'Не указано'),
                    'phone': metadata.get('phone', ''),
                    'address': metadata.get('address', ''),
                    'city': metadata.get('city', ''),
                    'website': metadata.get('website', ''),
                    'description': metadata.get('description', '')
                }
                logger.debug(f"Данные для организации: {organization_data}")
                org_serializer = OrganizationSerializer(data=organization_data)
                if not org_serializer.is_valid():
                    logger.error(f"Ошибка валидации организации: {org_serializer.errors}")
                    return Response({"errors": org_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                organization = org_serializer.save()
                logger.info(f"Создана организация: {organization.name}")

                building_data = {
                    'organization': organization.id,
                    'name': 'Главный корпус',
                    'address': metadata.get('address', ''),
                    'phone': metadata.get('phone', ''),
                    'email': metadata.get('email', 'Не указано')
                }
                logger.debug(f"Данные для корпуса: {building_data}")
                building_serializer = BuildingSerializer(data=building_data)
                if not building_serializer.is_valid():
                    logger.error(f"Ошибка валидации корпуса: {building_serializer.errors}")
                    return Response({"errors": building_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                building = building_serializer.save()
                logger.info(f"Создан корпус: {building.name}")

                admin_emails = CustomUser.objects.filter(role='admin_app').values_list('email', flat=True)
                if not admin_emails:
                    logger.warning("Не найдено пользователей с ролью admin_app для уведомления об оплате")
                    return Response(status=status.HTTP_200_OK)

                html_message = render_to_string('email/payment_success_email.html', {
                    'logo_url': settings.LOGO_URL,
                    'organization_name': organization.name,
                    'organization_email': organization.email,
                    'amount_value': payment.amount.value,
                    'amount_currency': payment.amount.currency,
                    'payment_id': payment.id,
                    'organization_address': organization.address,
                    'organization_city': organization.city,
                    'admin_url': f"{settings.FRONTEND_URL}/admin",
                    'support_url': settings.SUPPORT_URL,
                    'year': timezone.now().year,
                })

                subject = "Оплачена новая организация!"
                message = (
                    f"Новая организация успешно оплатила регистрацию:\n\n"
                    f"Название: {organization.name}\n"
                    f"Email: {organization.email}\n"
                    f"Сумма: {payment.amount.value} {payment.amount.currency}\n"
                    f"ID платежа: {payment.id}\n"
                    f"Адрес: {organization.address}\n"
                    f"Город: {organization.city}\n\n"
                    f"Свяжитесь с администрацией организации для уточнения деталей."
                )

                send_email_task.delay(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=list(admin_emails),
                    html_message=html_message
                )
                logger.info(f"Оплата {payment.id} обработана, организация создана, уведомления отправлены администраторам")

                return Response(status=status.HTTP_200_OK)
            else:
                logger.info(f"Игнорируем вебхук с событием: {notification.event}")
                return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Инициация оплаты",
        description="Создаёт платёж через ЮKassa для регистрации учебного заведения. Возвращает URL для перенаправления на страницу оплаты.",
        request={
            "type": "object",
            "properties": {
                "institutionName": {"type": "string", "description": "Название организации"},
                "email": {"type": "string", "description": "Email организации"},
                "phone": {"type": "string", "description": "Телефон организации"},
                "address": {"type": "string", "description": "Адрес организации"},
                "city": {"type": "string", "description": "Город организации"},
                "website": {"type": "string", "description": "Веб-сайт организации"},
                "description": {"type": "string", "description": "Описание организации"},
                "return_url": {"type": "string", "description": "URL возврата после оплаты"}
            },
            "required": ["institutionName", "email"]
        },
        responses={
            200: OpenApiResponse(
                description="Платёж успешно инициирован",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "payment_url": "https://yookassa.ru/checkout?payment_id=123456789",
                            "payment_id": "123456789"
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "institutionName": "Университет",
                    "email": "contact@university.ru",
                    "phone": "+79991234567",
                    "address": "ул. Ленина, 10",
                    "city": "Москва",
                    "website": "www.university.ru",
                    "description": "Ведущий вуз",
                    "return_url": "https://applicantcabinet.ru/payment-success"
                }
            )
        ]
    )
    def post(self, request):
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                "value": "4000.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": request.data.get('return_url', 'https://applicantcabinet.ru/payment-success')
            },
            "capture": True,
            "description": "Оплата регистрации учебного заведения",
            "metadata": {
                "institution_name": request.data.get('institutionName', ''),
                "email": request.data.get('email', ''),
                "phone": request.data.get('phone', ''),
                "address": request.data.get('address', ''),
                "city": request.data.get('city', ''),
                "website": request.data.get('website', ''),
                "description": request.data.get('description', '')
            }
        }, idempotence_key)

        logger.info(f"Инициирована оплата: {payment.id} для {request.data.get('institutionName')}")
        return Response({
            "payment_url": payment.confirmation.confirmation_url,
            "payment_id": payment.id
        }, status=status.HTTP_200_OK)

class OrganizationApplicationView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Подача заявки на регистрацию организации",
        description="Отправляет заявку на регистрацию организации администраторам системы. После проверки администратор создаст организацию.",
        request=OrganizationSerializer,
        responses={
            200: OpenApiResponse(
                description="Заявка успешно отправлена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Заявка успешно отправлена. Администратор свяжется с вами после проверки."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"name": ["Это поле обязательно"]}
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Ошибка сервера",
                examples=[
                    OpenApiExample(
                        name="Ошибка 500",
                        value={"message": "Нет доступных администраторов для обработки запроса"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "name": "Университет",
                    "email": "contact@university.ru",
                    "phone": "+79991234567",
                    "address": "ул. Ленина, 10",
                    "city": "Москва",
                    "website": "www.university.ru",
                    "description": "Ведущий вуз",
                    "institutionType": "Университет"
                }
            )
        ]
    )
    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        admin_emails = CustomUser.objects.filter(role='admin_app').values_list('email', flat=True)
        if not admin_emails:
            logger.error("Не найдено пользователей с ролью admin_app для обработки заявки на организацию")
            return Response(
                {"message": "Нет доступных администраторов для обработки запроса"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        subject = "Новая заявка на регистрацию организации"
        message = (
            f"Получена новая заявка на регистрацию организации:\n\n"
            f"Название: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Телефон: {data['phone']}\n"
            f"Адрес: {data['address']}\n"
            f"Веб-сайт: {data.get('website', 'Не указан')}\n"
            f"Описание: {data.get('description', 'Не указано')}\n"
            f"Тип учреждения: {request.data.get('institutionType', 'Не указан')}\n\n"
            f"Пожалуйста, создайте организацию в системе после проверки."
        )

        send_email_task.delay(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(admin_emails)
        )
        logger.info(f"Задача отправки email поставлена в очередь для заявки на организацию: {data['name']}")

        return Response(
            {"message": "Заявка успешно отправлена. Администратор свяжется с вами после проверки."},
            status=status.HTTP_200_OK
        )

class OrganizationView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp | IsAdminOrg]

    @extend_schema(
        summary="Получение списка организаций",
        description="Возвращает список организаций. Для admin_app — все организации, для admin_org — только организация пользователя. Данные кэшируются на 1 час.",
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
                                "description": "Ведущий вуз"
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно прав или нет привязанной организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "У пользователя нет назначенной организации или недостаточно прав"}
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
        cache_key = f"organizations_{request.user.role}_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Попадание в кэш для {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        if request.user.role == 'admin_app':
            organizations = Organization.objects.all()
            logger.info(f"AdminApp {request.user.email} получил все организации с корпусами")
        elif request.user.role == 'admin_org' and request.user.organization:
            organizations = Organization.objects.filter(id=request.user.organization.id)
            logger.info(f"AdminOrg {request.user.email} получил организацию {request.user.organization.name}")
        else:
            raise ValidationError("У пользователя нет назначенной организации или недостаточно прав")

        serializer = OrganizationSerializer(organizations, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создание организации",
        description="Создаёт новую организацию. Доступно для admin_app или admin_org.",
        request=OrganizationSerializer,
        responses={
            201: OpenApiResponse(
                description="Организация успешно создана",
                response=OrganizationSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "name": "Университет",
                            "email": "contact@university.ru",
                            "phone": "+79991234567",
                            "address": "ул. Ленина, 10",
                            "city": "Москва",
                            "website": "www.university.ru",
                            "description": "Ведущий вуз"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"name": ["Это поле обязательно"]}
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
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "name": "Университет",
                    "email": "contact@university.ru",
                    "phone": "+79991234567",
                    "address": "ул. Ленина, 10",
                    "city": "Москва",
                    "website": "www.university.ru",
                    "description": "Ведущий вуз"
                }
            )
        ]
    )
    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Обновление организации",
        description="Частично обновляет данные организации по её идентификатору. Доступно для admin_app или admin_org.",
        request=OrganizationSerializer,
        responses={
            200: OpenApiResponse(
                description="Организация успешно обновлена",
                response=OrganizationSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "name": "Университет",
                            "email": "new@university.ru",
                            "phone": "+79991234567",
                            "address": "ул. Ленина, 10",
                            "city": "Москва",
                            "website": "www.university.ru",
                            "description": "Ведущий вуз"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"id": ["Это поле обязательно"]}
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
                    "id": 1,
                    "email": "new@university.ru"
                }
            )
        ]
    )
    def patch(self, request):
        organization = Organization.objects.get(id=request.data.get('id'))
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление организации",
        description="Удаляет организацию по её идентификатору. Доступно для admin_app или admin_org.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор организации",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Организация успешно удалена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Организация удалена"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "Идентификатор обязателен"}
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
        }
    )
    def delete(self, request):
        organization = Organization.objects.get(id=request.query_params.get('id'))
        organization.delete()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response({'message': 'Организация удалена'}, status=status.HTTP_204_NO_CONTENT)

class BuildingView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg | IsAdminApp]

    @extend_schema(
        summary="Получение списка корпусов",
        description="Возвращает список корпусов. Для admin_app — все корпуса, для admin_org — корпуса организации пользователя. Данные кэшируются на 1 час.",
        responses={
            200: OpenApiResponse(
                description="Список корпусов успешно получен",
                response=BuildingSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "name": "Главный корпус",
                                "address": "ул. Ленина, 10",
                                "phone": "+79991234567",
                                "email": "info@university.ru",
                                "organization": 1
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно прав или нет привязанной организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "У пользователя нет назначенной организации или недостаточно прав"}
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
        cache_key = f"buildings_{request.user.role}_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Попадание в кэш для {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        if request.user.role == 'admin_app':
            buildings = Building.objects.all()
            logger.info(f"AdminApp {request.user.email} получил все корпуса")
        elif request.user.organization:
            buildings = Building.objects.filter(organization=request.user.organization)
            logger.info(f"Получено {len(buildings)} корпусов для организации {request.user.organization.name}")
        else:
            raise ValidationError("У пользователя нет назначенной организации или недостаточно прав")

        serializer = BuildingSerializer(buildings, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создание корпуса",
        description="Создаёт новый корпус для организации. Отправляется уведомление на email пользователя.",
        request=BuildingSerializer,
        responses={
            201: OpenApiResponse(
                description="Корпус успешно создан",
                response=BuildingSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "name": "Главный корпус",
                            "address": "ул. Ленина, 10",
                            "phone": "+79991234567",
                            "email": "info@university.ru",
                            "organization": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"name": ["Это поле обязательно"]}
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
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "name": "Главный корпус",
                    "address": "ул. Ленина, 10",
                    "phone": "+79991234567",
                    "email": "info@university.ru",
                    "organization": 1
                }
            )
        ]
    )
    def post(self, request):
        logger.debug(f"BuildingView POST запрос данные: {request.data}")
        serializer = BuildingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building = serializer.save()

        subject = "Создан новый корпус"
        message = f"Корпус {building.name} создан для {building.organization.name}. ID: {building.id}"
        send_email_task.delay(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email]
        )
        logger.info(f"Задача отправки email поставлена в очередь для корпуса {building.name}")

        logger.info(f"Корпус {building.name} создан пользователем {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Обновление корпуса",
        description="Частично обновляет данные корпуса по его идентификатору. Доступно для admin_app или admin_org.",
        request=BuildingSerializer,
        responses={
            200: OpenApiResponse(
                description="Корпус успешно обновлён",
                response=BuildingSerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "name": "Главный корпус",
                            "address": "ул. Ленина, 20",
                            "phone": "+79991234567",
                            "email": "info@university.ru",
                            "organization": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или ID отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID корпуса обязателен"}
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
                description="Корпус не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Building matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "id": 1,
                    "address": "ул. Ленина, 20"
                }
            )
        ]
    )
    def patch(self, request):
        building_id = request.data.get('id')
        if not building_id:
            raise ValidationError("ID корпуса обязателен")

        if request.user.role == 'admin_app':
            building = Building.objects.get(id=building_id)
        elif request.user.organization:
            building = Building.objects.get(id=building_id, organization=request.user.organization)
        else:
            raise ValidationError("У пользователя нет назначенной организации или недостаточно прав")

        serializer = BuildingSerializer(building, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Корпус {building_id} обновлен пользователем {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление корпуса",
        description="Удаляет корпус по его идентификатору. Доступно для admin_app или admin_org.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор корпуса",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Корпус успешно удалён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Корпус удален"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID корпуса обязателен"}
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
                description="Корпус не найден",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Building matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request):
        building_id = request.query_params.get('id')
        if not building_id:
            raise ValidationError("ID корпуса обязателен")

        if request.user.role == 'admin_app':
            building = Building.objects.get(id=building_id)
        elif request.user.organization:
            building = Building.objects.get(id=building_id, organization=request.user.organization)
        else:
            raise ValidationError("У пользователя нет назначенной организации или недостаточно прав")

        building.delete()
        logger.info(f"Корпус {building_id} удален пользователем {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response({'message': 'Корпус удален'}, status=status.HTTP_204_NO_CONTENT)

class SpecialtyView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Получение списка специальностей",
        description="Возвращает список специальностей организации пользователя. Данные кэшируются на 1 час.",
        responses={
            200: OpenApiResponse(
                description="Список специальностей успешно получен",
                response=SpecialtySerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "code": "09.03.01",
                                "name": "Информатика",
                                "organization": 1
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Нет привязанной организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "У пользователя нет назначенной организации"}
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
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        cache_key = f"specialties_org_{request.user.organization.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Попадание в кэш для {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        specialties = Specialty.objects.filter(organization=request.user.organization)
        serializer = SpecialtySerializer(specialties, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Получено {len(specialties)} специальностей для организации {request.user.organization.name}")
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Создание специальности",
        description="Создаёт новую специальность для организации пользователя.",
        request=SpecialtySerializer,
        responses={
            201: OpenApiResponse(
                description="Специальность успешно создана",
                response=SpecialtySerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "code": "09.03.01",
                            "name": "Информатика",
                            "organization": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или нет прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"code": ["Это поле обязательно"]}
                    ),
                    OpenApiExample(
                        name="Ошибка организации",
                        value={"detail": "У пользователя нет назначенной организации"}
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
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "code": "09.03.01",
                    "name": "Информатика",
                    "organization": 1
                }
            )
        ]
    )
    def post(self, request):
        if not request.user.is_authenticated:
            raise ValidationError("Требуется аутентификация")

        if not hasattr(request.user, 'organization') or not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        logger.info(f"Данные запроса: {request.data}")
        data = request.data.copy()
        if 'organization' in data:
            data['organization_id'] = data.pop('organization')

        serializer = SpecialtySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        specialty = serializer.save()
        logger.info(f"Специальность {specialty.code} - {specialty.name} создана пользователем {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Обновление специальности",
        description="Частично обновляет данные специальности по её идентификатору.",
        request=SpecialtySerializer,
        responses={
            200: OpenApiResponse(
                description="Специальность успешно обновлена",
                response=SpecialtySerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "code": "09.03.01",
                            "name": "Информатика и вычислительная техника",
                            "organization": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или ID отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID специальности обязателен"}
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
                description="Специальность не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No Specialty matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "id": 1,
                    "name": "Информатика и вычислительная техника"
                }
            )
        ]
    )
    def patch(self, request):
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        specialty_id = request.data.get('id')
        if not specialty_id:
            raise ValidationError("ID специальности обязателен")
        specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
        serializer = SpecialtySerializer(specialty, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Специальность {specialty_id} обновлена пользователем {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление специальности",
        description="Удаляет специальность по её идентификатору.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор специальности",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Специальность успешно удалена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "Специальность удалена"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID специальности обязателен"}
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
    def delete(self, request):
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        specialty_id = request.query_params.get('id')
        if not specialty_id:
            raise ValidationError("ID специальности обязателен")
        specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
        specialty.delete()
        logger.info(f"Специальность {specialty_id} удалена пользователем {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response({'message': 'Специальность удалена'}, status=status.HTTP_204_NO_CONTENT)

class BuildingSpecialtyView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    @extend_schema(
        summary="Создание связи специальности с корпусом",
        description="Создаёт связь между специальностью и корпусом для организации пользователя.",
        request=BuildingSpecialtySerializer,
        responses={
            201: OpenApiResponse(
                description="Связь успешно создана",
                response=BuildingSpecialtySerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "building": 1,
                            "specialty": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или нет прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={"building": ["Это поле обязательно"]}
                    ),
                    OpenApiExample(
                        name="Ошибка организации",
                        value={"detail": "У пользователя нет назначенной организации"}
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
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "building": 1,
                    "specialty": 1
                }
            )
        ]
    )
    def post(self, request):
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        serializer = BuildingSpecialtySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building_specialty = serializer.save()
        logger.info(
            f"Специальность {building_specialty.specialty.name} назначена корпусу {building_specialty.building.name} пользователем {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Обновление связи специальности с корпусом",
        description="Частично обновляет данные связи между специальностью и корпусом по её идентификатору.",
        request=BuildingSpecialtySerializer,
        responses={
            200: OpenApiResponse(
                description="Связь успешно обновлена",
                response=BuildingSpecialtySerializer,
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "id": 1,
                            "building": 1,
                            "specialty": 2
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или ID отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID BuildingSpecialty обязателен"}
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
                description="Связь не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No BuildingSpecialty matches the given query."}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "id": 1,
                    "specialty": 2
                }
            )
        ]
    )
    def patch(self, request):
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        building_specialty_id = request.data.get('id')
        if not building_specialty_id:
            raise ValidationError("ID BuildingSpecialty обязателен")
        building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                           building__organization=request.user.organization)
        serializer = BuildingSpecialtySerializer(building_specialty, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"BuildingSpecialty {building_specialty_id} обновлен пользователем {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление связи специальности с корпусом",
        description="Удаляет связь между специальностью и корпусом по её идентификатору.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="Идентификатор связи BuildingSpecialty",
                required=True,
                examples=[
                    OpenApiExample(name="Пример ID", value=1)
                ]
            )
        ],
        responses={
            204: OpenApiResponse(
                description="Связь успешно удалена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={"message": "BuildingSpecialty удален"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Идентификатор отсутствует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "ID BuildingSpecialty обязателен"}
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
                description="Связь не найдена",
                examples=[
                    OpenApiExample(
                        name="Ошибка 404",
                        value={"detail": "No BuildingSpecialty matches the given query."}
                    )
                ]
            )
        }
    )
    def delete(self, request):
        if not request.user.organization:
            raise ValidationError("У пользователя нет назначенной организации")

        building_specialty_id = request.query_params.get('id')
        if not building_specialty_id:
            raise ValidationError("ID BuildingSpecialty обязателен")
        building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                           building__organization=request.user.organization)
        building_specialty.delete()
        logger.info(f"BuildingSpecialty {building_specialty_id} удален пользователем {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response({'message': 'BuildingSpecialty удален'}, status=status.HTTP_204_NO_CONTENT)