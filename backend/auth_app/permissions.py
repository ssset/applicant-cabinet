from rest_framework import permissions
from users.models import CustomUser


class IsAdminApp(permissions.BasePermission):
    """
    Разрешение для admin_app: полный доступ.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin_app'


class IsAdminOrg(permissions.BasePermission):
    """
    Разрешение для admin_org: доступ к данным своей организации.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin_org'


class IsModerator(permissions.BasePermission):
    """
    Разрешение для moderator: доступ к заявкам своей организации.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'moderator'


class IsApplicant(permissions.BasePermission):
    """
    Разрешение для applicant: доступ только к своим данным.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'applicant'


class IsEmailVerified(permissions.BasePermission):
    """
    Проверка, что email пользователя верифицирован.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified


