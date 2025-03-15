import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, ApplicantProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsApplicant, IsEmailVerified
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from users.models import ApplicantProfile

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