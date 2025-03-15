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
        # Пропускаем запросы на регистрацию и верификацию
        if request.path in ['/api/auth/register/', '/api/auth/verify/']:
            return self.get_response(request)

        if request.user.is_authenticated and not request.user.is_verified:
            return JsonResponse({'message': 'Email not verified'}, status=status.HTTP_403_FORBIDDEN)

        return self.get_response(request)


class RoleBasedAccessMiddleware:
    """
    Middleware для проверки роли пользователя.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем запросы на регистрацию и верификацию
        if request.path in ['/api/auth/register/', '/api/auth/verify/']:
            return self.get_response(request)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        # Разрешаем доступ для admin_app ко всем эндпоинтам
        if request.user.role == 'admin_app':
            return self.get_response(request)

        # Для других ролей проверяем доступ к /api/profile/
        if request.path == '/api/profile/' and request.user.role == 'applicant':
            return self.get_response(request)

        # Временное ограничение: только applicant имеет доступ к /api/profile/
        return JsonResponse({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
