# org/serializers.py
from rest_framework import serializers
from .models import Organization, Building, Specialty, BuildingSpecialty

class OrganizationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для организации.
    """
    class Meta:
        model = Organization
        fields = ['id', 'name', 'email', 'phone', 'address', 'created_at', 'updated_at']


class BuildingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления данными корпуса.
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


class BuildingSpecialtySerializer(serializers.ModelSerializer):
    """
    Сериализатор для связи специальности с корпусом.
    """
    class Meta:
        model = BuildingSpecialty
        fields = ['id', 'building', 'specialty', 'budget_places', 'commercial_places', 'commercial_price']
        extra_kwargs = {
            'building': {'required': True},
            'specialty': {'required': True}
        }

    def validate(self, data):
        # Проверяем, что корпус принадлежит той же организации, что и специальность
        if data['building'].organization != data['specialty'].organization:
            raise serializers.ValidationError('Building and Specialty must belong to the same organization.')
        return data


class SpecialtySerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления специальностями.
    """
    building_specialties = BuildingSpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = Specialty
        fields = ['id', 'organization', 'code', 'name', 'created_at', 'updated_at', 'building_specialties']
        extra_kwargs = {
            'organization': {'required': True, 'write_only': True}
        }

    def validate(self, data):
        # Проверяем уникальность кода специальности в рамках организации
        if 'organization' in data and 'code' in data:
            if self.instance:
                if Specialty.objects.filter(
                        organization=data['organization'],
                        code=data['code']
                ).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError('A specialty with this code already exists in the organization.')
            else:
                if Specialty.objects.filter(organization=data['organization'], code=data['code']).exists():
                    raise serializers.ValidationError('A specialty with this code already exists in the organization.')
        return data