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

# Настройка ЮKassa
Configuration.account_id = settings.YUKASSA_SHOP_ID
Configuration.secret_key = settings.YUKASSA_SECRET_KEY

class PaymentWebhookView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            notification = WebhookNotification(request.data)
            if notification.event == 'payment.succeeded':
                payment = notification.object
                metadata = payment.metadata

                # Создание организации
                organization_data = {
                    'name': metadata.get('institution_name', 'Не указано'),
                    'email': metadata.get('email', 'Не указано'),
                    'phone': metadata.get('phone', ''),
                    'address': metadata.get('address', ''),
                    'city': metadata.get('city', ''),
                    'website': metadata.get('website', ''),
                    'description': metadata.get('description', '')
                }
                org_serializer = OrganizationSerializer(data=organization_data)
                org_serializer.is_valid(raise_exception=True)
                organization = org_serializer.save()

                # Создание корпуса
                building_data = {
                    'organization': organization.id,
                    'name': 'Главный корпус',
                    'address': metadata.get('address', ''),
                    'phone': metadata.get('phone', ''),
                    'email': metadata.get('email', 'Не указано')
                }
                building_serializer = BuildingSerializer(data=building_data)
                building_serializer.is_valid(raise_exception=True)
                building = building_serializer.save()

                admin_emails = CustomUser.objects.filter(role='admin_app').values_list('email', flat=True)
                if not admin_emails:
                    logger.error("Не найдено пользователей с ролью admin_app для уведомления об оплате")
                    return Response(status=status.HTTP_200_OK)

                # Рендеринг HTML-шаблона для письма
                html_message = render_to_string('email/payment_success_email.html', {
                    'logo_url': settings.LOGO_URL,  # Убедитесь, что это определено в настройках
                    'organization_name': organization.name,
                    'organization_email': organization.email,
                    'amount_value': payment.amount.value,
                    'amount_currency': payment.amount.currency,
                    'payment_id': payment.id,
                    'organization_address': organization.address,
                    'organization_city': organization.city,
                    'admin_url': f"{settings.FRONTEND_URL}/admin",  # URL панели администратора
                    'support_url': settings.SUPPORT_URL,  # Убедитесь, что это определено
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
        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PaymentView(APIView):
    permission_classes = []

    def post(self, request):
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                "value": "2000.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": request.data.get('return_url', 'http://localhost:3000/payment-success')
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

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        organization = Organization.objects.get(id=request.data.get('id'))
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        organization = Organization.objects.get(id=request.query_params.get('id'))
        organization.delete()
        cache.delete("organizations_all")
        cache.delete_pattern("organizations_*")
        return Response({'message': 'Организация удалена'}, status=status.HTTP_204_NO_CONTENT)

class BuildingView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg | IsAdminApp]

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