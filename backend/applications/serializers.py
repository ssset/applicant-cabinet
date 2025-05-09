# applications/serializers.py
from rest_framework import serializers
from .models import Application
from org.models import BuildingSpecialty
from org.serializers import BuildingSpecialtySerializer
from users.models import ApplicantProfile
from users.serializers import ApplicantProfileSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    building_specialty = BuildingSpecialtySerializer(read_only=True)
    building_specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=BuildingSpecialty.objects.all(),
        source='building_specialty',
        write_only=True,
        required=True
    )
    applicant_profile = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'applicant', 'applicant_profile', 'building_specialty', 'building_specialty_id',
            'priority', 'course', 'study_form', 'funding_basis',
            'dormitory_needed', 'first_time_education', 'info_source',
            'status', 'reject_reason', 'created_at', 'updated_at'  # Добавляем reject_reason
        ]
        extra_kwargs = {
            'applicant': {'read_only': True},
            'status': {'read_only': True},
            'reject_reason': {'read_only': True}  # Делаем поле только для чтения
        }

    def get_applicant_profile(self, obj):
        try:
            profile = ApplicantProfile.objects.get(user=obj.applicant)
            return ApplicantProfileSerializer(profile).data
        except ApplicantProfile.DoesNotExist:
            return None

    def validate(self, data):
        applicant = self.context['request'].user
        building_specialty = data.get('building_specialty')

        if applicant.role != 'applicant':
            raise serializers.ValidationError('Only applicants can submit applications.')

        # Подсчитываем все заявки на эту специальность в этом корпусе
        existing_applications = Application.objects.filter(
            applicant=applicant,
            building_specialty=building_specialty
        )

        # Проверяем количество попыток (максимум 3, включая текущую)
        if len(existing_applications) >= 3:
            raise serializers.ValidationError(
                'You have reached the maximum number of application attempts (3) for this specialty.'
            )

        if self.instance is None:  # Создание новой заявки
            # Проверяем, есть ли среди существующих заявок те, которые не отклонены
            non_rejected_applications = existing_applications.exclude(status='rejected')
            if non_rejected_applications.exists():
                raise serializers.ValidationError(
                    'You cannot apply to this specialty because you have a non-rejected application.'
                )

        # Проверка доступности мест
        if data.get('funding_basis') == 'budget' and building_specialty.budget_places <= 0:
            raise serializers.ValidationError('No budget places available for this specialty.')
        if data.get('funding_basis') == 'commercial' and building_specialty.commercial_places <= 0:
            raise serializers.ValidationError('No commercial places available for this specialty.')

        return data

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для лидерборда по специальности.
    """
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    applicant_profile = serializers.SerializerMethodField()
    building_specialty = BuildingSpecialtySerializer(read_only=True)
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'applicant', 'applicant_email', 'applicant_profile',
            'building_specialty', 'priority', 'status', 'created_at', 'rank'
        ]

    def get_applicant_profile(self, obj):
        try:
            profile = ApplicantProfile.objects.get(user=obj.applicant)
            return ApplicantProfileSerializer(profile).data
        except ApplicantProfile.DoesNotExist:
            return None

    def get_rank(self, obj):
        """
        Возвращает место заявки в лидерборде (заполняется в view).
        """
        return getattr(obj, 'rank', None)