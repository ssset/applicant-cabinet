import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant, IsModerator, IsAdminOrg
from org.models import Specialty, BuildingSpecialty, Organization
from org.serializers import SpecialtySerializer, BuildingSpecialtySerializer
from org.serializers import OrganizationSerializer
from .models import Application
from users.models import ApplicantProfile
from .serializers import ApplicationSerializer, LeaderboardSerializer
from django.core.cache import cache
from applicant.tasks import send_email_task  # Импортируем задачу
from django.conf import settings

logger = logging.getLogger(__name__)

class ApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

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

    def post(self, request):
        if not ApplicantProfile.objects.filter(user=request.user).exists():
            logger.warning(f"User {request.user.email} attempted to submit an application without a profile")
            raise ValidationError({"message": "Вы должны заполнить профиль абитуриента перед подачей заявления."})

        serializer = ApplicationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        logger.info(f"Application {application.id} submitted by {request.user.email}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    def get(self, request):
        specialty_id = request.query_params.get('id')
        organization_id = request.query_params.get('organization_id')
        city = request.query_params.get('city')  # Добавляем параметр city

        # Формируем ключ кэша с учетом city
        cache_key = f"specialties_{organization_id or 'all'}_{city or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data is not None and not specialty_id:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        specialties = Specialty.objects.all()

        # Фильтрация по organization_id, если указан
        if organization_id:
            specialties = specialties.filter(organization_id=organization_id)

        # Фильтрация по city, если указан
        if city:
            specialties = specialties.filter(organization__city__iexact=city)

        if specialty_id:
            specialty = specialties.get(id=specialty_id)
            serializer = SpecialtySerializer(specialty)
            logger.info(f"Retrieved specialty {specialty_id} for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = SpecialtySerializer(specialties, many=True)
        data = serializer.data
        if not specialty_id:  # Кэшируем только список специальностей, а не одиночную
            cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(specialties)} specialties for {request.user.email} with city {city or 'all'}")
        return Response(data, status=status.HTTP_200_OK)

class AvailableCitiesView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        cache_key = "available_cities"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        cities = Organization.objects.values_list('city', flat=True).distinct()
        cities = [city for city in cities if city]  # Убираем пустые значения
        data = sorted(cities)
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(data)} unique cities for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class ApplicationAttemptsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

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

    def get(self, request):
        city = request.query_params.get('city')

        # Динамический ключ кэша в зависимости от city
        cache_key = f"organizations_{city or 'all'}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        organizations = Organization.objects.all()

        # Фильтрация по city, если указан
        if city:
            organizations = organizations.filter(city__iexact=city)

        serializer = OrganizationSerializer(organizations, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved {len(organizations)} organizations for {request.user.email} with city {city or 'all'}")
        return Response(data, status=status.HTTP_200_OK)

class ModeratorApplicationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

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

        # Отправляем email-уведомление абитуриенту
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

        # Логирование роли и организации пользователя для диагностики
        logger.info(f"User {request.user.email} role: {request.user.role}, organization: {getattr(request.user, 'organization', 'None')}")
        if request.user.role == 'admin_org' and not getattr(request.user, 'organization', None):
            logger.warning(f"Admin_org {request.user.email} has no organization assigned")

        # Проверка, что building_specialty принадлежит организации пользователя для admin_org
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