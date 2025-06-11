import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from .serializers import ApplicantProfileSerializer, CustomUserSerializer, AdminOrgListSerializer
from auth_app.serializers import RegisterSerializer
from .models import CustomUser, ApplicantProfile
from auth_app.permissions import IsApplicant, IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
from org.models import Organization
from applicant.tasks import process_attestation_image_task  # Импортируем задачу
from django.core.cache import cache
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

class ApplicantProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        logger.debug(f"GET /api/users/profile/ for user {request.user.id}")
        profile = ApplicantProfile.objects.filter(user=request.user).first()
        if not profile:
            logger.info(f"No profile found for user {request.user.id}")
            return Response(
                {"message": "Профиль абитуриента еще не создан"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ApplicantProfileSerializer(profile)
        logger.debug(f"Returning profile data for user {request.user.id}: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        logger.debug(f"POST /api/users/profile/ for user {request.user.id}, data={request.data}")
        if ApplicantProfile.objects.filter(user=request.user).exists():
            logger.error(f"Profile already exists for user {request.user.id}")
            raise ValidationError("Profile already exists")

        serializer = ApplicantProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(user=request.user)

        if 'attestation_photo' in request.FILES:
            logger.info(
                f"New attestation photo uploaded for user {request.user.id} "
                f"(profile {profile.id}), path: {profile.attestation_photo.path}"
            )
            task = process_attestation_image_task.delay(profile.id, profile.attestation_photo.path)
            logger.info(f"Task {task.id} started for processing attestation photo for user {request.user.id}")
            profile.task_id = task.id
            profile.save()
        else:
            logger.info(f"No attestation photo in request for user {request.user.id}")

        logger.debug(f"Created profile for user {request.user.id}: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        logger.debug(f"PATCH /api/users/profile/ for user {request.user.id}, data={request.data}")
        profile = ApplicantProfile.objects.get(user=request.user)
        serializer = ApplicantProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        if 'attestation_photo' in request.FILES:
            logger.info(f"Attestation photo updated via PATCH for user {request.user.id} (profile {profile.id})")
            task = process_attestation_image_task.delay(profile.id,
                                                        profile.attestation_photo.path)  # Добавляем profile.id
            profile.task_id = str(task.id)
            profile.save()

        logger.debug(f"Updated profile for user {request.user.id}: {serializer.data}")
        return Response(ApplicantProfileSerializer(profile).data, status=status.HTTP_200_OK)
    def delete(self, request):
        logger.debug(f"DELETE /api/users/profile/ for user {request.user.id}")
        profile = ApplicantProfile.objects.get(user=request.user)
        profile.delete()
        logger.info(f"Profile deleted for user {request.user.id}")
        return Response({'message': 'Profile deleted'}, status=status.HTTP_204_NO_CONTENT)

class AdminAppCreationView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        if CustomUser.objects.filter(role='admin_app').exists():
            raise ValidationError("Admin app already exists")

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'admin_app'
        user.save()
        return Response({
            'message': 'Admin app registered, check your email for verification code'
        }, status=status.HTTP_201_CREATED)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f"current_user_{request.user.id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        serializer = CustomUserSerializer(request.user)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(f"current_user_{request.user.id}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminOrgView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'admin_org'
        organization_id = request.data.get('organization_id')
        organization = Organization.objects.get(id=organization_id)
        user.organization = organization
        user.save()
        return Response({
            'message': 'Admin org registered, check your email for verification code'
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        logger.info("Fetching admin_org users")
        admin_orgs = CustomUser.objects.filter(role='admin_org')
        serializer = AdminOrgListSerializer(admin_orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id=None):
        logger.info(f"AdminOrgView PATCH: user={request.user}, id={id}, data={request.data}")
        if id is None:
            raise ValidationError("User ID is required")

        admin_org = CustomUser.objects.get(id=id, role='admin_org')
        serializer = RegisterSerializer(admin_org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        organization_id = request.data.get('organization_id')
        if organization_id:
            organization = Organization.objects.get(id=organization_id)
            admin_org.organization = organization
            admin_org.save()
        serializer.save()
        logger.info(f"Admin org with id {id} updated by {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id=None):
        if id is None:
            raise ValidationError("User ID is required")

        admin_org = CustomUser.objects.get(id=id, role='admin_org')
        admin_org.delete()
        logger.info(f"Admin org with id {id} deleted by {request.user.email}")
        return Response({'message': 'Admin org deleted'}, status=status.HTTP_204_NO_CONTENT)

class ModeratorView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def post(self, request):
        logger.info(f'Creating moderator with data: {request.data}')
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.role = 'moderator'
        user.organization = request.user.organization
        user.save()
        return Response({
            'message': 'Moderator registered, check email for verification code'
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        logger.info(f"Fetching moderators for organization: {request.user.organization}")
        moderators = CustomUser.objects.filter(role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderators, many=True)
        logger.info(f"moderators info: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        logger.info(
            f"ModeratorView PATCH: user={request.user}, authenticated={request.user.is_authenticated}, organization={request.user.organization}")
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        user_id = request.data.get('id')
        if not user_id:
            raise ValidationError("User ID is required")

        moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderator, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user_id = request.query_params.get('id')
        if not user_id:
            raise ValidationError("User ID is required")

        moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
        moderator.delete()
        return Response({'message': 'Moderator deleted'}, status=status.HTTP_204_NO_CONTENT)


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_id = request.query_params.get('task_id')
        logger.debug(f"GET /api/task-status/?task_id={task_id} for user {request.user.id}")
        if not task_id:
            logger.error("Task ID is required")
            return Response({"error": "Task ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(task_id)
        logger.debug(f"Task {task_id} state: {task.state}")
        if task.state == 'PENDING':
            response = {'status': 'pending'}
        elif task.state == 'SUCCESS':
            result = task.result
            logger.debug(f"Task {task_id} result: {result}")
            if isinstance(result, dict) and "error" in result:
                response = {'status': 'failed', 'error': result["error"]}
            else:
                response = {'status': 'completed', 'result': result}
                if task.name == 'applicant.tasks.process_attestation_image_task':
                    try:
                        profile = request.user.applicantprofile
                        profile.calculated_average_grade = result
                        print(result, "ВОТ РЕЗУЛЬТААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААААТ")
                        profile.task_id = None
                        profile.save()
                        logger.info(f"Updated profile for user {request.user.id} with average grade {result}")
                    except Exception as e:
                        logger.error(f"Failed to update profile for user {request.user.id}: {str(e)}", exc_info=True)
        else:
            response = {'status': 'failed', 'error': str(task.result)}
            logger.error(f"Task {task_id} failed: {str(task.result)}")

        logger.info(f"Task {task_id} status checked: {response}")
        return Response(response, status=status.HTTP_200_OK)