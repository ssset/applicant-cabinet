# users/serializers.py
from rest_framework import serializers
from .models import ApplicantProfile, CustomUser
from org.models import Organization
from org.serializers import OrganizationSerializer


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
            'average_grade', 'calculated_average_grade',
            'foreign_languages', 'attestation_photo', 'additional_info',
            'mother_full_name', 'mother_workplace', 'mother_phone',
            'father_full_name', 'father_workplace', 'father_phone'
        ]
        read_only_fields = ['calculated_average_grade']  # Поле только для чтения

    def validate_foreign_languages(self, value):
        if value and not isinstance(value, list):
            raise serializers.ValidationError('Foreign languages must be a list')
        return value

    def validate_average_grade(self, value):
        if value is not None:
            if value < 0 or value > 5.0:
                raise serializers.ValidationError('Average grade must be between 0 and 5.0')
        return value


class AdminOrgListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка admin_org, используемый в AdminOrgView.get.
    """
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role', 'organization', 'is_verified', 'consent_to_data_processing']
        read_only_fields = ['role', 'is_verified', 'organization']


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели CustomUser.
    """
    class Meta:
        model = CustomUser
        fields = ['email', 'role', 'is_verified', 'consent_to_data_processing']
        read_only_fields = ['role', 'is_verified']  # Поля, которые нельзя изменять через PATCH