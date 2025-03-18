from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth import get_user_model
import logging


logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"EmailVerificationMiddleware: path={request.path}, user={request.user}, authenticated={request.user.is_authenticated}, headers={dict(request.headers)}")
        # Пропускаем пути, не требующие аутентификации
        if request.path in ['/api/auth/register/', '/api/auth/verify/', '/api/auth/admin-app/create/', '/api/auth/login/']:
            logger.info("Bypassing email verification for registration/verify/login paths")
            return self.get_response(request)

        # Даём JWTAuthentication шанс обработать токен перед проверкой
        response = self.get_response(request)

        # Проверяем верификацию только после обработки запроса, если пользователь аутентифицирован
        if request.user.is_authenticated and not request.user.is_verified and not hasattr(request, '_email_verification_skipped'):
            logger.warning(f"Email not verified for user: {request.user.email}")
            return JsonResponse({'message': 'Email not verified'}, status=status.HTTP_403_FORBIDDEN)

        return response


class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"RoleBasedAccessMiddleware: path={request.path}, user={request.user}, authenticated={request.user.is_authenticated}, headers={dict(request.headers)}")
        # Пропускаем пути, не требующие аутентификации
        if request.path in ['/api/auth/register/', '/api/auth/verify/', '/api/auth/admin-app/create/', '/api/auth/login/']:
            logger.info(f"Bypassing RoleBasedAccessMiddleware for path: {request.path}")
            return self.get_response(request)

        # Даём JWTAuthentication шанс обработать токен перед проверкой
        response = self.get_response(request)

        if not request.user.is_authenticated:
            logger.warning(f"User not authenticated, returning 401 for path: {request.path}")
            return JsonResponse({'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            if request.path.startswith('/api/auth/moderators/') and request.user.role != 'admin_org':
                logger.warning(f"Access denied for user {request.user.email} with role {request.user.role}")
                return JsonResponse({'message': 'Access denied: only admin_org can access moderators'}, status=status.HTTP_403_FORBIDDEN)

            if request.path == '/api/profile/' and request.user.role != 'applicant':
                logger.warning(f"Access denied for user {request.user.email} with role {request.user.role}")
                return JsonResponse({'message': 'Access denied: only applicant can access profile'}, status=status.HTTP_403_FORBIDDEN)

            logger.info(f"Allowed access for user: {request.user.email} with role: {request.user.role}")
        except AttributeError:
            logger.error(f"User object has no role attribute: {request.user}")
            return JsonResponse({'message': 'Invalid user object'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response
