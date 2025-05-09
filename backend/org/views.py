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

                admin_emails = CustomUser.objects.filter(role='admin_app').values_list('email', flat=True)
                if not admin_emails:
                    logger.error("No admin_app users found for payment notification")
                    return Response(status=status.HTTP_200_OK)

                subject = "Успешная оплата регистрации организации"
                message = (
                    f"Получена оплата за регистрацию организации:\n\n"
                    f"Название: {metadata.get('institution_name', 'Не указано')}\n"
                    f"Email: {metadata.get('email', 'Не указано')}\n"
                    f"Сумма: {payment.amount.value} {payment.amount.currency}\n"
                    f"ID платежа: {payment.id}\n\n"
                    f"Пожалуйста, создайте организацию в системе."
                )

                send_email_task.delay(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=list(admin_emails)
                )
                logger.info(f"Payment {payment.id} processed, notification sent to admins")

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
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
                "return_url": request.data.get('return_url', 'http://localhost:3000/institutions-apply')
            },
            "capture": True,
            "description": "Оплата регистрации учебного заведения",
            "metadata": {
                "institution_name": request.data.get('institutionName', ''),
                "email": request.data.get('email', '')
            }
        }, idempotence_key)

        logger.info(f"Payment initiated: {payment.id} for {request.data.get('institutionName')}")
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
            logger.error("No admin_app users found for organization application")
            return Response(
                {"message": "No admin available to process the request"},
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
        logger.info(f"Email notification task queued for organization application: {data['name']}")

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
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        if request.user.role == 'admin_app':
            organizations = Organization.objects.all()
            logger.info(f"AdminApp {request.user.email} retrieved all organizations with buildings")
        elif request.user.role == 'admin_org' and request.user.organization:
            organizations = Organization.objects.filter(id=request.user.organization.id)
            logger.info(f"AdminOrg {request.user.email} retrieved organization {request.user.organization.name}")
        else:
            raise ValidationError("User has no organization assigned or insufficient permissions")

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
        return Response({'message': 'Organization deleted'}, status=status.HTTP_204_NO_CONTENT)


class BuildingView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg | IsAdminApp]

    def get(self, request):
        cache_key = f"buildings_{request.user.role}_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        if request.user.role == 'admin_app':
            buildings = Building.objects.all()
            logger.info(f"AdminApp {request.user.email} retrieved all buildings")
        elif request.user.organization:
            buildings = Building.objects.filter(organization=request.user.organization)
            logger.info(f"Retrieved {len(buildings)} buildings for organization {request.user.organization.name}")
        else:
            raise ValidationError("User has no organization assigned or insufficient permissions")

        serializer = BuildingSerializer(buildings, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        logger.debug(f"BuildingView POST request data: {request.data}")
        serializer = BuildingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building = serializer.save()

        subject = "New Building Created"
        message = f"Building {building.name} created for {building.organization.name}. ID: {building.id}"
        send_email_task.delay(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email]
        )
        logger.info(f"Email notification task queued for building {building.name}")

        logger.info(f"Building {building.name} created by {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        building_id = request.data.get('id')
        if not building_id:
            raise ValidationError("Building ID is required")

        if request.user.role == 'admin_app':
            building = Building.objects.get(id=building_id)
        elif request.user.organization:
            building = Building.objects.get(id=building_id, organization=request.user.organization)
        else:
            raise ValidationError("User has no organization assigned or insufficient permissions")

        serializer = BuildingSerializer(building, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Building {building_id} updated by {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        building_id = request.query_params.get('id')
        if not building_id:
            raise ValidationError("Building ID is required")

        if request.user.role == 'admin_app':
            building = Building.objects.get(id=building_id)
        elif request.user.organization:
            building = Building.objects.get(id=building_id, organization=request.user.organization)
        else:
            raise ValidationError("User has no organization assigned or insufficient permissions")

        building.delete()
        logger.info(f"Building {building_id} deleted by {request.user.email}")
        cache.delete_pattern("buildings_*")
        return Response({'message': 'Building deleted'}, status=status.HTTP_204_NO_CONTENT)


class SpecialtyView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        cache_key = f"specialties_org_{request.user.organization.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        specialties = Specialty.objects.filter(organization=request.user.organization)
        serializer = SpecialtySerializer(specialties, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(specialties)} specialties for organization {request.user.organization.name}")
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_authenticated:
            raise ValidationError("Authentication required")

        if not hasattr(request.user, 'organization') or not request.user.organization:
            raise ValidationError("User has no organization assigned")

        logger.info(f"Request data: {request.data}")
        data = request.data.copy()
        if 'organization' in data:
            data['organization_id'] = data.pop('organization')

        serializer = SpecialtySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        specialty = serializer.save()
        logger.info(f"Specialty {specialty.code} - {specialty.name} created by {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        specialty_id = request.data.get('id')
        if not specialty_id:
            raise ValidationError("Specialty ID is required")
        specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
        serializer = SpecialtySerializer(specialty, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Specialty {specialty_id} updated by {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        specialty_id = request.query_params.get('id')
        if not specialty_id:
            raise ValidationError("Specialty ID is required")
        specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
        specialty.delete()
        logger.info(f"Specialty {specialty_id} deleted by {request.user.email}")
        cache.delete_pattern("specialties_*")
        return Response({'message': 'Specialty deleted'}, status=status.HTTP_204_NO_CONTENT)


class BuildingSpecialtyView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def post(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        serializer = BuildingSpecialtySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building_specialty = serializer.save()
        logger.info(
            f"Specialty {building_specialty.specialty.name} assigned to building {building_specialty.building.name} by {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        building_specialty_id = request.data.get('id')
        if not building_specialty_id:
            raise ValidationError("BuildingSpecialty ID is required")
        building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                           building__organization=request.user.organization)
        serializer = BuildingSpecialtySerializer(building_specialty, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"BuildingSpecialty {building_specialty_id} updated by {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        building_specialty_id = request.query_params.get('id')
        if not building_specialty_id:
            raise ValidationError("BuildingSpecialty ID is required")
        building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                           building__organization=request.user.organization)
        building_specialty.delete()
        logger.info(f"BuildingSpecialty {building_specialty_id} deleted by {request.user.email}")
        cache.delete_pattern("leaderboard_*")
        return Response({'message': 'BuildingSpecialty deleted'}, status=status.HTTP_204_NO_CONTENT)