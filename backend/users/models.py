from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер для модели CustomUser, использующий email как уникальный идентификатор.
    """
    def create_user(self, email, password, role=None, **extra_fields):
        if not email:
            raise ValueError('The email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.role = role or 'applicant'
        user.verification_code = str(uuid.uuid4())[:8]
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


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
    verification_code = models.CharField(max_length=8, blank=True, null=True, verbose_name='Verification Code')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email