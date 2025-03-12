from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя с ролями и подтверждением email.
    """
    ROLES = (
        ('admin_app', 'Admin App'),
        ('admin_org', 'Admin Org'),
        ('moderator', 'Moderator'),
        ('applicant', 'Applicant'),
    )
    email = models.EmailField(unique=True, verbose_name='Email')
    role = models.CharField(max_length=20, choices=ROLES, default='applicant', verbose_name='Role')
    is_verified = models.BooleanField(default=False, verbose_name='Email Verified')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email