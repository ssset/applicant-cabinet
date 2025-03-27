# applications/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant, IsModerator
from org.models import Specialty, BuildingSpecialty
from org.serializers import SpecialtySerializer, BuildingSpecialtySerializer
from .models import Application
from .serializers import ApplicationSerializer

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
            if specialty_id:
                try:
                    specialty = Specialty.objects.get(id=specialty_id)
                    serializer = SpecialtySerializer(specialty)
                    logger.info(f"Retrieved specialty {specialty_id} for {request.user.email}")
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except Specialty.DoesNotExist:
                    logger.warning(f"Specialty {specialty_id} not found")
                    return Response({'error': 'Specialty not found'}, status=status.HTTP_404_NOT_FOUND)

            specialties = Specialty.objects.all()
            serializer = SpecialtySerializer(specialties, many=True)
            logger.info(f"Retrieved {len(specialties)} specialties for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specialties: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Новые вьюхи для модераторов
class ModeratorApplicationsView(APIView):
    """
    API для модераторов: получение списка всех заявок в их организации.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

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

class ModeratorApplicationDetailView(APIView):
    """
    API для модераторов: работа с одной заявкой (просмотр, переключение, принятие/отклонение).
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

    def get(self, request):
        """
        Получение данных по одной заявке с возможностью переключения.
        Параметры:
        - id: ID заявки.
        - direction (опционально): 'next' или 'prev' для переключения между заявками.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            application_id = request.query_params.get('id')
            direction = request.query_params.get('direction')  # 'next' или 'prev'

            # Получаем все заявки в организации, отсортированные по ID
            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization
            ).order_by('id')

            if not applications.exists():
                return Response({'error': 'No applications found'}, status=status.HTTP_404_NOT_FOUND)

            # Если передан direction, переключаемся на следующую/предыдущую заявку
            if direction:
                if not application_id:
                    raise ValidationError("Application ID is required for navigation")
                try:
                    current_application = applications.get(id=application_id)
                except Application.DoesNotExist:
                    logger.warning(f"Application {application_id} not found")
                    return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)

                # Находим индекс текущей заявки
                application_ids = list(applications.values_list('id', flat=True))
                current_index = application_ids.index(int(application_id))

                # Определяем ID следующей или предыдущей заявки
                if direction == 'next':
                    next_index = current_index + 1 if current_index + 1 < len(application_ids) else 0
                    application = applications[next_index]
                elif direction == 'prev':
                    prev_index = current_index - 1 if current_index - 1 >= 0 else len(application_ids) - 1
                    application = applications[prev_index]
                else:
                    raise ValidationError("Direction must be 'next' or 'prev'")
            else:
                # Если direction не передан, просто возвращаем заявку по ID
                if not application_id:
                    # Если ID не передан, возвращаем первую заявку
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
        """
        Принятие или отклонение заявки.
        Ожидаемые данные:
        - id: ID заявки.
        - action: 'accept' или 'reject'.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            application_id = request.data.get('id')
            action = request.data.get('action')

            if not application_id:
                raise ValidationError("Application ID is required")
            if not action:
                raise ValidationError("Action is required")

            application = Application.objects.get(
                id=application_id,
                building_specialty__building__organization=request.user.organization
            )

            if action == 'accept':
                application.status = 'accepted'
            elif action == 'reject':
                application.status = 'rejected'
            else:
                raise ValidationError("Action must be 'accept' or 'reject'")

            application.save()
            logger.info(f"Application {application.id} {action}ed by {request.user.email}")
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
