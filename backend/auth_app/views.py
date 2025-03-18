import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, ApplicantProfileSerializer, OrganizationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsApplicant, IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from users.models import ApplicantProfile, Organization

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterView(APIView):
    """
    API для регистрации нового пользователя.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        logger.info(f"Received request data: {request.data}")
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            logger.info("Serializer is valid")
            user = serializer.save()
            return Response({
                'message': 'User registered, check your email for verification code'
            }, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    API для проверки верификационного кода и подтверждения email.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('verification_code')
        try:
            user = User.objects.get(email=email)
            if user.verification_code == code and not user.is_verified:
                user.is_verified = True
                user.verification_code = None
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Email verified successfully',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }, status=status.HTTP_200_OK)

            elif user.is_verified:
                return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({'message': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


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
        if User.objects.filter(role='admin_app').exists():
            return Response ({'message': 'Admin app already exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'admin_app'
            user.save()
            return Response({
                'message': 'Admin app registered, check your email for verification code'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({'message':'Organization not found'}, status=status.HTTP_404_NOT_FOUND)


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


class LoginView(APIView):
    """
    API для входа пользователей с выдачей JWT токенов.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        logger.info(f'Login attempt with data: {request.data}')
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            if not user.is_verified:
                return Response({'message': 'Email is not verified'}, status=status.HTTP_401_UNAUTHORIZED)

            refresh = RefreshToken.for_user(user)
            response = Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
            response.set_cookie('refresh', str(refresh), httponly=True, secure=False)
            response.set_cookie('access', str(refresh.access_token), httponly=True, secure=False)
            logger.info(f'User {user.email} logged in successfully')
            return response

        logger.error(f'Invalid credentials for {email}')
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    API для выхода пользователя с удалением токенов из куки.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f'Logout attempt for user: {request.user.email}')
        response = Response({'message': 'Logged out'},status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        response.delete_cookie('access')
        logger.info(f'User {request.user.email} logged out successfully')
        return response


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
        moderators = User.objects.filter(role='moderator', organization=request.user.organization)
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

            moderator = User.objects.get(id=user_id, role='moderator', organization=request.user.organization)
            serializer = RegisterSerializer(moderator, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            logger.error(f"Moderator with id {user_id} not found")
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in ModeratorView.patch: {str(e)}")
            return Response({'message': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            user_id = request.query_params.get('id')
            moderator = User.objects.get(id=user_id, role= 'moderator', organization=request.user.organization)
            moderator.delete()
            return Response({'message': 'Moderator deleted'}, status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)
