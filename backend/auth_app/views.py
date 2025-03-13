from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterView(APIView):
    """
    Api для регистрации нового пользователя.
    """
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'User registered, check your email for verification code'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
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

                return Response({
                'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
            elif user.is_verified:
                return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message':'User not found'}, status=status.HTTP_404_NOT_FOUND)