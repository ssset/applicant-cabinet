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
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp | IsAdminOrg]

    def get(self, request):
        try:
            if request.user.role == 'admin_app':
                organizations = Organization.objects.all()
                logger.info(f"AdminApp {request.user.email} retrieved all organizations with buildings")
            elif request.user.role == 'admin_org' and request.user.organization:
                organizations = Organization.objects.filter(id=request.user.organization.id)
                logger.info(f"AdminOrg {request.user.email} retrieved organization {request.user.organization.name}")
            else:
                logger.error(f"User {request.user.email} has no organization assigned or insufficient permissions")
                return Response({'error': 'User has no organization assigned or insufficient permissions'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = OrganizationSerializer(organizations, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving organizations: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


# BuildingView остается без изменений, но добавим его для полноты
class BuildingView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg | IsAdminApp]

    def get(self, request):
        try:
            if request.user.role == 'admin_app':
                buildings = Building.objects.all()
                logger.info(f"AdminApp {request.user.email} retrieved all buildings")
            elif request.user.organization:
                buildings = Building.objects.filter(organization=request.user.organization)
                logger.info(f"Retrieved {len(buildings)} buildings for organization {request.user.organization.name}")
            else:
                logger.error(f"User {request.user.email} has no organization assigned and is not admin_app")
                return Response({'error': 'User has no organization assigned or insufficient permissions'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = BuildingSerializer(buildings, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving buildings: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            logger.debug(f"BuildingView POST request data: {request.data}")  # Добавлено для отладки
            serializer = BuildingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            building = serializer.save()

            subject = "New Building Created"
            message = f"Building {building.name} created for {building.organization.name}. ID: {building.id}"
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
            building_id = request.data.get('id')
            if not building_id:
                raise ValidationError("Building ID is required")

            if request.user.role == 'admin_app':
                building = Building.objects.get(id=building_id)
            elif request.user.organization:
                building = Building.objects.get(id=building_id, organization=request.user.organization)
            else:
                logger.error(f"User {request.user.email} has no organization assigned and is not admin_app")
                return Response({'error': 'User has no organization assigned or insufficient permissions'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = BuildingSerializer(building, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"Building {building_id} updated by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Building.DoesNotExist:
            logger.warning(f"Building {building_id} not found")
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.error(f"Validation error in BuildingView PATCH: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in BuildingView PATCH: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            building_id = request.query_params.get('id')
            if not building_id:
                raise ValidationError("Building ID is required")

            if request.user.role == 'admin_app':
                building = Building.objects.get(id=building_id)
            elif request.user.organization:
                building = Building.objects.get(id=building_id, organization=request.user.organization)
            else:
                logger.error(f"User {request.user.email} has no organization assigned and is not admin_app")
                return Response({'error': 'User has no organization assigned or insufficient permissions'},
                                status=status.HTTP_400_BAD_REQUEST)

            building.delete()
            logger.info(f"Building {building_id} deleted by {request.user.email}")
            return Response({'message': 'Building deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Building.DoesNotExist:
            logger.warning(f"Building {building_id} not found")
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
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

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
            # Проверяем, аутентифицирован ли пользователь
            if not request.user.is_authenticated:
                logger.error("User is not authenticated")
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            # Проверяем наличие организации у пользователя
            if not hasattr(request.user, 'organization') or not request.user.organization:
                logger.error(
                    f"User {request.user.email if hasattr(request.user, 'email') else 'unknown'} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Request data: {request.data}")
            data = request.data.copy()
            # Переименовываем organization в organization_id для сериализатора
            if 'organization' in data:
                data['organization_id'] = data.pop('organization')

            serializer = SpecialtySerializer(data=data)  # Убираем context
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
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg ]

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
