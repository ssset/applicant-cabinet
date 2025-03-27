# applications/serializers.py
from rest_framework import serializers
from .models import Application
from org.models import BuildingSpecialty  # Добавляем импорт модели
from org.serializers import BuildingSpecialtySerializer


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления заявками абитуриентов.
    """
    building_specialty = BuildingSpecialtySerializer(read_only=True)
    building_specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=BuildingSpecialty.objects.all(),
        source='building_specialty',
        write_only=True,
        required=True
    )

    class Meta:
        model = Application
        fields = [
            'id', 'applicant', 'building_specialty', 'building_specialty_id',
            'priority', 'course', 'study_form', 'funding_basis',
            'dormitory_needed', 'first_time_education', 'info_source',
            'status', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'applicant': {'read_only': True},
            'status': {'read_only': True}
        }

    def validate(self, data):
        """
        Проверка логики заявки.
        """
        applicant = self.context['request'].user
        building_specialty = data.get('building_specialty')

        # Проверяем, что пользователь - абитуриент
        if applicant.role != 'applicant':
            raise serializers.ValidationError('Only applicants can submit applications.')

        # Проверяем, не подал ли абитуриент заявку на эту специальность ранее
        if self.instance is None:  # Создание новой заявки
            if Application.objects.filter(applicant=applicant, building_specialty=building_specialty).exists():
                raise serializers.ValidationError('You have already applied to this specialty in this building.')

        # Проверяем доступные места
        if data.get('funding_basis') == 'budget' and building_specialty.budget_places <= 0:
            raise serializers.ValidationError('No budget places available for this specialty.')
        if data.get('funding_basis') == 'commercial' and building_specialty.commercial_places <= 0:
            raise serializers.ValidationError('No commercial places available for this specialty.')

        return data

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)