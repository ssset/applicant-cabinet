# org/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .serializers import OrganizationSerializer, BuildingSerializer
from auth_app.permissions import IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
from .models import Organization, Building
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class OrganizationView(APIView):
    """
    API для управления организациями (доступно только для admin_app)
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def get(self, request):
        organizations = Organization.objects.all()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            organization = Organization.objects.get(id=request.data.get('id'))
            serializer = OrganizationSerializer(organization, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Organization.DoesNotExist:
            return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        try:
            organization = Organization.objects.get(id=request.query_params.get('id'))
            organization.delete()
            return Response({'message': 'Organization deleted'}, status=status.HTTP_204_NO_CONTENT)

        except Organization.DoesNotExist:
            return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

class BuildingView(APIView):
    """
    API для управления корпусами (доступно только для admin_org).
    Поддерживает CRUD операции с отправкой уведомления на email при создании.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
            buildings = Building.objects.filter(organization=request.user.organization)
            serializer = BuildingSerializer(buildings, many=True)
            logger.info(f"Retrieved {len(buildings)} buildings for organization {request.user.organization.name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving buildings: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            data = request.data.copy()
            data['organization'] = request.user.organization.id
            serializer = BuildingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            building = serializer.save()

            # Отправка уведомления
            subject = "New Building Created"
            message = f"Building {building.name} created for {request.user.organization.name}. ID: {building.id}"
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                logger.info(f"Email notification sent to {request.user.email} for building {building.name}")
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
                # Не прерываем выполнение, если email не отправился
                pass

            logger.info(f"Building {building.name} created by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            building_id = request.data.get('id')
            if not building_id:
                raise ValidationError("Building ID is required")
            building = Building.objects.get(id=building_id, organization=request.user.organization)
            serializer = BuildingSerializer(building, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"Building {building_id} updated by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Building.DoesNotExist:
            logger.warning(f"Building {building_id} not found for {request.user.organization.name}")
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingView PATCH: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingView PATCH: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            building_id = request.query_params.get('id')
            if not building_id:
                raise ValidationError("Building ID is required")
            building = Building.objects.get(id=building_id, organization=request.user.organization)
            building.delete()
            logger.info(f"Building {building_id} deleted by {request.user.email}")
            return Response({'message': 'Building deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Building.DoesNotExist:
            logger.warning(f"Building {building_id} not found for {request.user.organization.name}")
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingView DELETE: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingView DELETE: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
