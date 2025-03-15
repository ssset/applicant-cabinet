from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailVerificationMiddleware:
    """
    Middleware для проверки верификации email.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Пропускаем запросы на регистрацию и верификацию."""

        if request.path in ['/api/auth/register', 'api/auth/verify']:
            return self.get_response(request)

        if request.user.is_authenticated and not request.user.is_verified:
            return JsonResponse({'message': 'Email is not verified'}, status=status.HTTP_403_FORBIDDEN)

        return self.get_response(request)


class RoleBasedAcessMiddleware:
    """
    Middleware для проверки роли пользователя.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Пропускаем запросы на регистрацию и верификацию."""

        if request.path in ['api/auth/register', 'api/auth/verify']:
            return self.get_response(request)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role == 'applicant' and request.user.path not in ['api/profile']:
            return JsonResponse({'message': 'Access denied for applicants'}, status=status.HTTP_403_FORBIDDEN)

        return self.get_response(request)