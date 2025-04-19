# applications/views.py
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
from .serializers import ApplicationSerializer, LeaderboardSerializer

logger = logging.getLogger(__name__)

# Существующие вьюхи (ApplicationView и AvailableSpecialtiesView)
class ApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        try:
            applications = Application.objects.filter(applicant=request.user)
            serializer = ApplicationSerializer(applications, many=True)
            logger.info(f"Retrieved {len(applications)} applications for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving applications for {request.user.email}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = ApplicationSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            application = serializer.save()
            logger.info(f"Application {application.id} submitted by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in ApplicationView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ApplicationView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            application_id = request.query_params.get('id')
            if not application_id:
                raise ValidationError("Application ID is required")
            application = Application.objects.get(id=application_id, applicant=request.user)
            if application.status != 'pending':
                raise ValidationError("Cannot delete an application that is already accepted or rejected")
            application.delete()
            logger.info(f"Application {application_id} deleted by {request.user.email}")
            return Response({'message': 'Application deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Application.DoesNotExist:
            logger.warning(f"Application {application_id} not found for {request.user.email}")
            return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in ApplicationView DELETE: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ApplicationView DELETE: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableSpecialtiesView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        try:
            specialty_id = request.query_params.get('id')
            organization_id = request.query_params.get('organization_id')  # Добавляем параметр

            specialties = Specialty.objects.all()
            if organization_id:
                specialties = specialties.filter(organization_id=organization_id)

            if specialty_id:
                try:
                    specialty = specialties.get(id=specialty_id)
                    serializer = SpecialtySerializer(specialty)
                    logger.info(f"Retrieved specialty {specialty_id} for {request.user.email}")
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except Specialty.DoesNotExist:
                    logger.warning(f"Specialty {specialty_id} not found")
                    return Response({'error': 'Specialty not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = SpecialtySerializer(specialties, many=True)
            logger.info(f"Retrieved {len(specialties)} specialties for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specialties: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableOrganizationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        try:
            organizations = Organization.objects.all()
            serializer = OrganizationSerializer(organizations, many=True)
            logger.info(f"Retrieved {len(organizations)} organizations for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving organizations: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Новые вьюхи для модераторов
class ModeratorApplicationsView(APIView):
    """
    API для модераторов: получение списка всех заявок в их организации.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        """
        Получение списка заявок, поданных в организацию модератора.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization
            )
            serializer = ApplicationSerializer(applications, many=True)
            logger.info(f"Retrieved {len(applications)} applications for organization {request.user.organization.name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving applications: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# applications/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant, IsModerator, IsAdminOrg
from org.models import Specialty, BuildingSpecialty
from org.serializers import SpecialtySerializer, BuildingSpecialtySerializer
from .models import Application
from .serializers import ApplicationSerializer, LeaderboardSerializer

logger = logging.getLogger(__name__)

# ... (предыдущие вьюхи без изменений) ...

class ModeratorApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            application_id = request.query_params.get('id')
            direction = request.query_params.get('direction')

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization
            ).order_by('id')

            if not applications.exists():
                return Response({'error': 'No applications found'}, status=status.HTTP_404_NOT_FOUND)

            if direction:
                if not application_id:
                    raise ValidationError("Application ID is required for navigation")
                try:
                    current_application = applications.get(id=application_id)
                except Application.DoesNotExist:
                    logger.warning(f"Application {application_id} not found")
                    return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

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
                    try:
                        application = applications.get(id=application_id)
                    except Application.DoesNotExist:
                        logger.warning(f"Application {application_id} not found")
                        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = ApplicationSerializer(application)
            logger.info(f"Retrieved application {application.id} for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.error(f"Validation error in ModeratorApplicationDetailView GET: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ModeratorApplicationDetailView GET: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            application_id = request.data.get('id')
            action = request.data.get('action')
            reject_reason = request.data.get('reject_reason')  # Получаем причину отклонения

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
                application.reject_reason = None  # Очищаем причину, если заявка принимается
            elif action == 'reject':
                application.status = 'rejected'
                application.reject_reason = reject_reason
            else:
                raise ValidationError("Action must be 'accept' or 'reject'")

            application.save()
            logger.info(f"Application {application.id} {action}ed by {request.user.email} with reason: {reject_reason}")
            return Response({'message': f'Application {action}ed'}, status=status.HTTP_200_OK)
        except Application.DoesNotExist:
            logger.warning(f"Application {application_id} not found")
            return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in ModeratorApplicationDetailView PATCH: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in ModeratorApplicationDetailView PATCH: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeaderboardView(APIView):
    """
    API для получения лидерборда по специальности.
    Доступно только для абитуриентов.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        """
        Получение лидерборда для конкретной специальности.
        Параметры:
        - building_specialty_id: ID специальности в корпусе (обязательный).
        """
        try:
            building_specialty_id = request.query_params.get('building_specialty_id')
            if not building_specialty_id:
                raise ValidationError("Building specialty ID is required")

            # Проверяем, существует ли building_specialty
            try:
                building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id)
            except BuildingSpecialty.DoesNotExist:
                logger.warning(f"BuildingSpecialty {building_specialty_id} not found")
                return Response({'error': 'Building specialty not found'}, status=status.HTTP_404_NOT_FOUND)

            # Получаем все заявки для этой специальности
            applications = Application.objects.filter(
                building_specialty=building_specialty
            ).order_by(
                # Сортировка: сначала по статусу (accepted -> pending -> rejected),
                # затем по приоритету, затем по дате подачи
                '-status', 'priority', 'created_at'
            )

            # Добавляем rank (место в рейтинге)
            ranked_applications = []
            for rank, application in enumerate(applications, start=1):
                application.rank = rank
                ranked_applications.append(application)

            serializer = LeaderboardSerializer(ranked_applications, many=True)
            logger.info(f"Retrieved leaderboard for BuildingSpecialty {building_specialty_id}")
            return Response({
                'building_specialty': BuildingSpecialtySerializer(building_specialty).data,
                'leaderboard': serializer.data,
                'user_rank': self.get_user_rank(request.user, ranked_applications)
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.error(f"Validation error in LeaderboardView GET: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in LeaderboardView GET: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_user_rank(self, user, ranked_applications):
        """
        Возвращает место пользователя в лидерборде.
        """
        for application in ranked_applications:
            if application.applicant == user:
                return application.rank
        return None

