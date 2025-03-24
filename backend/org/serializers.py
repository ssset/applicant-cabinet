# org/serializers.py
from rest_framework import serializers
from .models import Organization, Building

class OrganizationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для организации.
    """
    class Meta:
        model = Organization
        fields = ['id', 'name', 'email', 'phone', 'address', 'created_at', 'updated_at']

class BuildingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления данными корпуса
    """
    class Meta:
        model = Building
        fields = ['id', 'organization', 'name', 'address', 'phone', 'email', 'created_at', 'updated_at']
        extra_kwargs = {
            'organization': {'required': True, 'write_only': True}
        }

    def validate(self, data):
        # Если это частичное обновление и organization не передан, используем текущую organization объекта
        if self.partial and 'organization' not in data:
            if self.instance:
                data['organization'] = self.instance.organization
            else:
                raise serializers.ValidationError("Organization is required for validation")

        # Проверяем уникальность только если переданы organization и name
        if 'organization' in data and 'name' in data:
            # Если это обновление, исключаем текущий объект из проверки уникальности
            if self.instance:
                if Building.objects.filter(
                        organization=data['organization'],
                        name=data['name']
                ).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('A building with this name already exists in the organization')
            else:
                if Building.objects.filter(organization=data['organization'], name=data['name']).exists():
                    raise serializers.ValidationError('A building with this name already exists in the organization')

        return data
