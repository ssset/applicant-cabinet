# users/serializers.py
from rest_framework import serializers
from .models import ApplicantProfile


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