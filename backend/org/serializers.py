# org/serializers.py
from rest_framework import serializers
from .models import Organization, Building, Specialty, BuildingSpecialty

class BuildingSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=True,
        write_only=True
    )

    class Meta:
        model = Building
        fields = ['id', 'organization', 'name', 'address', 'phone', 'email', 'created_at', 'updated_at']
        extra_kwargs = {
            'organization': {'required': True}
        }

    def validate(self, data):
        if self.partial and 'organization' not in data:
            if self.instance:
                data['organization'] = self.instance.organization
            else:
                raise serializers.ValidationError("Organization is required for validation")
        if 'organization' in data and 'name' in data:
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


class OrganizationSerializer(serializers.ModelSerializer):
    buildings = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = ['id', 'name', 'email', 'phone', 'address', 'website', 'description', 'created_at', 'updated_at', 'buildings', 'city']
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
            'address': {'required': True},
            'city': {'required': True},  # Добавляем city как обязательное поле
        }

    def validate_email(self, value):
        if Organization.objects.filter(email=value).exists():
            raise serializers.ValidationError("Organization with this email already exists.")
        return value


class SimpleSpecialtySerializer(serializers.ModelSerializer):
    """
    Упрощённый сериализатор для Specialty без building_specialties, чтобы избежать рекурсии.
    """
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Specialty
        fields = ['id', 'organization', 'code', 'name', 'created_at', 'updated_at', 'duration', 'requirements']
        extra_kwargs = {
            'organization': {'required': True, 'write_only': False}
        }

    def validate(self, data):
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

class BuildingSpecialtySerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    specialty = SimpleSpecialtySerializer(read_only=True)
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), source='building', write_only=True
    )

    class Meta:
        model = BuildingSpecialty
        fields = ['id', 'building', 'building_id', 'specialty', 'budget_places', 'commercial_places', 'commercial_price']
        extra_kwargs = {
            'building': {'required': False},
            'specialty': {'required': False}
        }

    def validate(self, data):
        if 'building' in data and 'specialty' in data:
            if data['building'].organization != data['specialty'].organization:
                raise serializers.ValidationError('Building and Specialty must belong to the same organization.')
        return data

class SpecialtySerializer(serializers.ModelSerializer):
    building_specialties = BuildingSpecialtySerializer(many=True, read_only=False, required=False)
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source='organization',
        write_only=True,
        required=True,
        error_messages={'does_not_exist': 'Указанная организация не существует.'}
    )

    class Meta:
        model = Specialty
        fields = ['id', 'organization', 'organization_id', 'code', 'name', 'created_at', 'updated_at', 'building_specialties', 'duration', 'requirements']
        extra_kwargs = {
            'code': {'required': True},
            'name': {'required': True},
        }

    def validate(self, data):
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

    def create(self, validated_data):
        building_specialties_data = validated_data.pop('building_specialties', [])
        specialty = Specialty.objects.create(**validated_data)
        for bs_data in building_specialties_data:
            BuildingSpecialty.objects.create(specialty=specialty, **bs_data)
        return specialty

    def update(self, instance, validated_data):
        building_specialties_data = validated_data.pop('building_specialties', None)
        instance = super().update(instance, validated_data)
        if building_specialties_data is not None:
            instance.building_specialties.all().delete()
            for bs_data in building_specialties_data:
                BuildingSpecialty.objects.create(specialty=instance, **bs_data)
        return instance