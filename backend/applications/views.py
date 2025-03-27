import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsApplicant
from org.models import Specialty, BuildingSpecialty
from org.serializers import SpecialtySerializer, BuildingSpecialtySerializer
from .models import Application
from .serializers import ApplicationSerializer

logger = logging.getLogger(__name__)


class ApplicationView(APIView):
    """
    API для подачи заявок абитуриентами.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        """
        Получение списка заявок абитуриента.
        """
        try:
            applications = Application.objects.filter(applicant=request.user)
            serializer = ApplicationSerializer(applications, many=True)
            logger.info(f"Retrieved {len(applications)} applications for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving applications for {request.user.email}: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Подача новой заявки.
        """
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
        """
        Удаление заявки.
        """
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
    """
    API для отображения доступных специальностей.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        """
        Получение списка доступных специальностей.
        """
        try:
            specialties = Specialty.objects.all()
            serializer = SpecialtySerializer(specialties, many=True)
            logger.info(f"Retrieved {len(specialties)} specialties for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specialties: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
