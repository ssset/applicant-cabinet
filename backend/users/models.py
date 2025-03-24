# users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер для модели CustomUser, использующий email как уникальный идентификатор.
    """
    def create_user(self, email, password, consent_to_data_processing=None, role=None, organization=None, **extra_fields):
        if not email:
            raise ValueError('The email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.role = role or 'applicant'
        user.verification_code = str(uuid.uuid4())[:8]
        user.consent_to_data_processing = consent_to_data_processing
        if organization:
            user.organization = organization
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
    consent_to_data_processing = models.BooleanField(default=False, verbose_name='Consent to Data Processing')
    organization = models.ForeignKey('org.Organization', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Organization')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

class ApplicantProfile(models.Model):
    """
    Профиль абитуриента с личными данными и документами.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='applicant_profile',
                                verbose_name='User')
    photo = models.ImageField(upload_to='applicant_photos/', blank=True, null=True, verbose_name='Photo')
    first_name = models.CharField(max_length=50, blank=True, verbose_name='First Name')
    last_name = models.CharField(max_length=50, blank=True, verbose_name='Last Name')
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Middle Name')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Date of Birth')
    citizenship = models.CharField(max_length=50, blank=True, verbose_name='Citizenship')
    birth_place = models.CharField(max_length=100, blank=True, verbose_name='Place of Birth')
    # Документ, удостоверяющий личность
    passport_series = models.CharField(max_length=10, blank=True, verbose_name='Passport Series')
    passport_number = models.CharField(max_length=20, blank=True, verbose_name='Passport Number')
    passport_issued_date = models.DateField(blank=True, null=True, verbose_name='Passport Issued Date')
    passport_issued_by = models.CharField(max_length=100, blank=True, verbose_name='Passport Issued By')
    snils = models.CharField(max_length=20, blank=True, verbose_name='SNILS')
    # Адреса
    registration_address = models.TextField(blank=True, verbose_name='Registration Address')
    actual_address = models.TextField(blank=True, verbose_name='Actual Address')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Phone')
    # Образование
    education_type = models.CharField(max_length=50, blank=True, verbose_name='Education Type', choices=[
        ('school', 'School'),
        ('npo', 'NPO'),
        ('other', 'Other'),
    ])
    education_institution = models.CharField(max_length=100, blank=True, verbose_name='Education Institution')
    graduation_year = models.IntegerField(blank=True, null=True, verbose_name='Graduation Year')
    document_type = models.CharField(max_length=20, blank=True, verbose_name='Document Type', choices=[
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
    ])
    document_series = models.CharField(max_length=10, blank=True, verbose_name='Document Series')
    document_number = models.CharField(max_length=20, blank=True, verbose_name='Document Number')
    # Дополнительная информация
    foreign_languages = models.JSONField(blank=True, null=True, verbose_name='Foreign Languages')  # Список языков
    attestation_photo = models.ImageField(upload_to='attestations/', blank=True, null=True,
                                          verbose_name='Attestation Photo')
    additional_info = models.TextField(blank=True, verbose_name='Additional Info')
    # Родители
    mother_full_name = models.CharField(max_length=100, blank=True, verbose_name='Mother Full Name')
    mother_workplace = models.CharField(max_length=100, blank=True, verbose_name='Mother Workplace')
    mother_phone = models.CharField(max_length=20, blank=True, verbose_name='Mother Phone')
    father_full_name = models.CharField(max_length=100, blank=True, verbose_name='Father Full Name')
    father_workplace = models.CharField(max_length=100, blank=True, verbose_name='Father Workplace')
    father_phone = models.CharField(max_length=20, blank=True, verbose_name='Father Phone')

    class Meta:
        verbose_name = 'Applicant Profile'
        verbose_name_plural = 'Applicant Profiles'

    def __str__(self):
        return f'Profile of {self.user}'