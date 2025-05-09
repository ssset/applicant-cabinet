
# auth/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate

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
                'message': 'User registered, check your email for verification link'
            }, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response({'message': 'Пользователь с таким Email уже существует'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    """
    API для проверки верификационного токена и подтверждения email.
    """
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'message': 'Verification token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(verification_token=token)
            if user.is_verified:
                return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.verification_token = None  # Очищаем токен после верификации
            user.save()
            return Response({
                'message': 'Email verified successfully',
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'message': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)

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
                'access': str(refresh.access_token),
                'role': user.role  # Добавляем роль в тело ответа
            }, status=status.HTTP_200_OK)
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
        response = Response({'message': 'Logged out'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        response.delete_cookie('access')
        logger.info(f'User {request.user.email} logged out successfully')
        return response
