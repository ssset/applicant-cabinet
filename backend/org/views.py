# org/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .serializers import OrganizationSerializer, BuildingSerializer, SpecialtySerializer, BuildingSpecialtySerializer
from auth_app.permissions import IsEmailVerified, IsAdminApp, IsAdminOrg, IsModerator
from rest_framework.permissions import IsAuthenticated
from .models import Organization, Building, Specialty, BuildingSpecialty
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


class SpecialtyView(APIView):
    """
    API для управления специальностями (доступно только для модераторов).
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

    def get(self, request):
        """
        Получение списка специальностей для организации модератора.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)
            specialties = Specialty.objects.filter(organization=request.user.organization)
            serializer = SpecialtySerializer(specialties, many=True)
            logger.info(f"Retrieved {len(specialties)} specialties for organization {request.user.organization.name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specialties: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Создание новой специальности.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            data = request.data.copy()
            data['organization'] = request.user.organization.id
            serializer = SpecialtySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            specialty = serializer.save()
            logger.info(f"Specialty {specialty.code} - {specialty.name} created by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in SpecialtyView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in SpecialtyView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """
        Обновление специальности.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            specialty_id = request.data.get('id')
            if not specialty_id:
                raise ValidationError("Specialty ID is required")
            specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
            serializer = SpecialtySerializer(specialty, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"Specialty {specialty_id} updated by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Specialty.DoesNotExist:
            logger.warning(f"Specialty {specialty_id} not found for {request.user.organization.name}")
            return Response({'error': 'Specialty not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in SpecialtyView PATCH: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in SpecialtyView PATCH: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        Удаление специальности.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            specialty_id = request.query_params.get('id')
            if not specialty_id:
                raise ValidationError("Specialty ID is required")
            specialty = Specialty.objects.get(id=specialty_id, organization=request.user.organization)
            specialty.delete()
            logger.info(f"Specialty {specialty_id} deleted by {request.user.email}")
            return Response({'message': 'Specialty deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Specialty.DoesNotExist:
            logger.warning(f"Specialty {specialty_id} not found for {request.user.organization.name}")
            return Response({'error': 'Specialty not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in SpecialtyView DELETE: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in SpecialtyView DELETE: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BuildingSpecialtyView(APIView):
    """
    API для привязки специальностей к корпусам (доступно только для модераторов).
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator]

    def post(self, request):
        """
        Привязка специальности к корпусу.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = BuildingSpecialtySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            building_specialty = serializer.save()
            logger.info(f"Specialty {building_specialty.specialty.name} assigned to building {building_specialty.building.name} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingSpecialtyView POST: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingSpecialtyView POST: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """
        Обновление данных о местах и цене для специальности в корпусе.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            building_specialty_id = request.data.get('id')
            if not building_specialty_id:
                raise ValidationError("BuildingSpecialty ID is required")
            building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                              building__organization=request.user.organization)
            serializer = BuildingSpecialtySerializer(building_specialty, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"BuildingSpecialty {building_specialty_id} updated by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BuildingSpecialty.DoesNotExist:
            logger.warning(f"BuildingSpecialty {building_specialty_id} not found for {request.user.organization.name}")
            return Response({'error': 'BuildingSpecialty not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingSpecialtyView PATCH: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingSpecialtyView PATCH: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        Удаление привязки специальности к корпусу.
        """
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            building_specialty_id = request.query_params.get('id')
            if not building_specialty_id:
                raise ValidationError("BuildingSpecialty ID is required")
            building_specialty = BuildingSpecialty.objects.get(id=building_specialty_id,
                                                              building__organization=request.user.organization)
            building_specialty.delete()
            logger.info(f"BuildingSpecialty {building_specialty_id} deleted by {request.user.email}")
            return Response({'message': 'BuildingSpecialty deleted'}, status=status.HTTP_204_NO_CONTENT)
        except BuildingSpecialty.DoesNotExist:
            logger.warning(f"BuildingSpecialty {building_specialty_id} not found for {request.user.organization.name}")
            return Response({'error': 'BuildingSpecialty not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingSpecialtyView DELETE: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingSpecialtyView DELETE: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
