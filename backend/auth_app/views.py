from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Регистрация нового пользователя",
        description="Создаёт нового пользователя с указанными данными (email, пароль, роль). После успешной регистрации отправляется письмо с ссылкой для подтверждения email.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Пользователь успешно зарегистрирован",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "User registered, check your email for verification link"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Некорректные данные или пользователь с таким email уже существует",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={
                            "message": "Пользователь с таким Email уже существует"
                        }
                    ),
                    OpenApiExample(
                        name="Ошибка валидации",
                        value={
                            "email": ["Это поле обязательно"],
                            "password": ["Пароль должен содержать минимум 8 символов"]
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "user@example.com",
                    "password": "strongpassword123",
                    "role": "applicant"
                }
            )
        ]
    )
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
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Подтверждение email",
        description="Подтверждает email пользователя по верификационному токену, переданному в параметре запроса. После успешного подтверждения токен очищается.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location="query",
                description="Верификационный токен, отправленный на email пользователя",
                required=True,
                examples=[
                    OpenApiExample(name="Пример токена", value="abc123def456")
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Email успешно подтверждён",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Email verified successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недействительный токен или email уже подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка токена",
                        value={"message": "Invalid verification token"}
                    ),
                    OpenApiExample(
                        name="Ошибка повторного подтверждения",
                        value={"message": "Email already verified"}
                    ),
                    OpenApiExample(
                        name="Ошибка отсутствия токена",
                        value={"message": "Verification token is required"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'message': 'Verification token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(verification_token=token)
            if user.is_verified:
                return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.verification_token = None
            user.save()
            return Response({
                'message': 'Email verified successfully',
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'message': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Вход пользователя",
        description="Аутентифицирует пользователя по email и паролю, возвращает JWT-токены (access и refresh) и роль пользователя. Требуется подтверждённый email.",
        request={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email пользователя"},
                "password": {"type": "string", "description": "Пароль пользователя"}
            },
            "required": ["email", "password"]
        },
        responses={
            200: OpenApiResponse(
                description="Успешный вход",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "role": "applicant"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неверные учетные данные или email не подтверждён",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"message": "Invalid credentials"}
                    ),
                    OpenApiExample(
                        name="Ошибка неподтверждённого email",
                        value={"message": "Email is not verified"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                name="Пример запроса",
                value={
                    "email": "user@example.com",
                    "password": "strongpassword123"
                }
            )
        ]
    )
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
                'role': user.role
            }, status=status.HTTP_200_OK)
            logger.info(f'User {user.email} logged in successfully')
            return response

        logger.error(f'Invalid credentials for {email}')
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход пользователя",
        description="Завершает сеанс пользователя, удаляя JWT-токены (access и refresh) из cookies.",
        responses={
            200: OpenApiResponse(
                description="Успешный выход",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value={
                            "message": "Logged out"
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            )
        }
    )
    def post(self, request):
        logger.info(f'Logout attempt for user: {request.user.email}')
        response = Response({'message': 'Logged out'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        response.delete_cookie('access')
        logger.info(f'User {request.user.email} logged out successfully')
        return response