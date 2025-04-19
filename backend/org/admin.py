# org/admin.py
from django.contrib import admin
from org.models import Organization, Building, Specialty, BuildingSpecialty

# Настройка админки для модели Organization
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'address')
    list_editable = ('email', 'phone', 'address')
    fields = ('name', 'email', 'phone', 'address', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

# Настройка админки для модели Building
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'address', 'phone', 'email', 'created_at', 'updated_at')
    list_filter = ('organization', 'created_at', 'updated_at')
    search_fields = ('name', 'address', 'phone', 'email')
    list_editable = ('address', 'phone', 'email')
    fields = ('organization', 'name', 'address', 'phone', 'email', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

# Настройка админки для модели Specialty
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке специальностей
    list_display = ('name', 'code', 'organization', 'duration', 'created_at', 'updated_at')

    # Поля, по которым можно фильтровать
    list_filter = ('organization', 'created_at', 'updated_at')

    # Поля, по которым можно искать
    search_fields = ('name', 'code')

    # Поля, которые можно редактировать прямо в списке
    list_editable = ('code', 'duration')

    # Поля, которые будут отображаться в форме редактирования
    fields = ('name', 'code', 'organization', 'duration', 'requirements', 'created_at', 'updated_at')

    # Поля, которые будут только для чтения
    readonly_fields = ('created_at', 'updated_at')

    # Количество элементов на странице
    list_per_page = 25

# Настройка админки для модели BuildingSpecialty
@admin.register(BuildingSpecialty)
class BuildingSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('specialty', 'building', 'budget_places', 'commercial_places', 'commercial_price')
    list_filter = ('building__organization', 'specialty')
    search_fields = ('specialty__name', 'building__name')
    list_editable = ('budget_places', 'commercial_places', 'commercial_price')
    fields = ('specialty', 'building', 'budget_places', 'commercial_places', 'commercial_price')
    list_per_page = 25