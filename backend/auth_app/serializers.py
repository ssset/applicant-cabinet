from rest_framework import serializers
from users.models import CustomUser, ApplicantProfile
from django.core.mail import send_mail


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    """
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2', 'role', 'consent_to_data_processing']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }

    def validate(self, data):
        """
        Проверка совпадения паролей.
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match')
        if not data.get('consent_to_data_processing', False):
            raise serializers.ValidationError('You must consent to data processing')
        return data

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'applicant'),
            consent_to_data_processing=validated_data['consent_to_data_processing']
        )

        send_mail(
            subject='Verify your email',
            message=f'Your verification code: {user.verification_code}',
            from_email='claimov@gmail.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        return user

class ApplicantProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля абитуриента.
    """
    class Meta:
        model = ApplicantProfile
        fields = [
            'photo', 'first_name', 'last_name', 'middle_name', 'date_of_birth',
            'citizenship', 'birth_place', 'passport_series', 'passport_number',
            'passport_issued_date', 'passport_issued_by', 'snils',
            'registration_address', 'actual_address', 'phone',
            'education_type', 'education_institution', 'graduation_year',
            'document_type', 'document_series', 'document_number',
            'foreign_languages', 'attestation_photo', 'additional_info',
            'mother_full_name', 'mother_workplace', 'mother_phone',
            'father_full_name', 'father_workplace', 'father_phone'
        ]

        def validate_foreign_languages(self, value):
            if value and not isinstance(value, list):
                raise serializers.ValidationError('Foreign languages must be a list')
            return value