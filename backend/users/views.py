# users/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from .serializers import ApplicantProfileSerializer
from auth_app.serializers import RegisterSerializer  # Импортируем из auth
from .models import CustomUser, ApplicantProfile
from auth_app.permissions import IsApplicant, IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
from org.models import Organization

logger = logging.getLogger(__name__)


class ApplicantProfileView(APIView):
    """
    API для управления профилем абитуриента.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            serializer = ApplicantProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            ApplicantProfile.objects.get(user=request.user)
            return Response({'message': 'Profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

        except ApplicantProfile.DoesNotExist:
            serializer = ApplicantProfileSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            serializer = ApplicantProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            profile.delete()
            return Response({'message': 'Profile deleted'}, status=status.HTTP_204_NO_CONTENT)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminAppCreationView(APIView):
    """
    API для создания первого admin_app.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        if CustomUser.objects.filter(role='admin_app').exists():
            return Response({'message': 'Admin app already exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'admin_app'
            user.save()
            return Response({
                'message': 'Admin app registered, check your email for verification code'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminOrgCreationView(APIView):
    """
    Api для создания admin_org (доступно только admin_app).
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'admin_org'
            organization_id = request.data.get('organization_id')
            try:
                organization = Organization.objects.get(id=organization_id)
                user.organization = organization
                user.save()
                return Response({
                    'message': 'Admin org registered, check your email for verification code'
                }, status=status.HTTP_201_CREATED)

            except Organization.DoesNotExist:
                user.delete()
                return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModeratorView(APIView):
    """
    API для управления модераторами (доступно только для admin_org)
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def post(self, request):
        logger.info(f'Creating moderator with data: {request.data}')
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'moderator'
            user.organization = request.user.organization
            user.save()
            return Response({
                'message': 'Moderator registered, check email for verification code'
            }, status=status.HTTP_201_CREATED)

        logger.error(f'Serializer errors: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        logger.info(f"Fetching moderators for organization: {request.user.organization}")
        moderators = CustomUser.objects.filter(role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderators, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        logger.info(f"ModeratorView PATCH: user={request.user}, authenticated={request.user.is_authenticated}, organization={request.user.organization}")
        if not request.user.organization:
            logger.error(f"User {request.user.email} has no organization assigned")
            return Response({'message': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = request.data.get('id')
            if not user_id:
                logger.error("No user_id provided in request data")
                return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
            serializer = RegisterSerializer(moderator, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            logger.error(f"Moderator with id {user_id} not found")
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in ModeratorView.patch: {str(e)}")
            return Response({'message': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            user_id = request.query_params.get('id')
            moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
            moderator.delete()
            return Response({'message': 'Moderator deleted'}, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist:
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)
