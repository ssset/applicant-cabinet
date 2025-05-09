from django.contrib import admin
from org.models import Organization, Building, Specialty, BuildingSpecialty
from django.core.cache import cache

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address', 'created_at', 'updated_at', 'city')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'address')
    list_editable = ('email', 'phone', 'address', 'city')
    fields = ('name', 'email', 'phone', 'address', 'created_at', 'updated_at', 'city')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Очистка кэша после сохранения
        cache.delete_pattern("organizations_*")
        cache.delete_pattern("available_*")

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'address', 'phone', 'email', 'created_at', 'updated_at')
    list_filter = ('organization', 'created_at', 'updated_at')
    search_fields = ('name', 'address', 'phone', 'email')
    list_editable = ('address', 'phone', 'email')
    fields = ('organization', 'name', 'address', 'phone', 'email', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

# Остальной код остается без изменений
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'duration', 'created_at', 'updated_at')
    list_filter = ('organization', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    list_editable = ('code', 'duration')
    fields = ('name', 'code', 'organization', 'duration', 'requirements', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

@admin.register(BuildingSpecialty)
class BuildingSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('specialty', 'building', 'budget_places', 'commercial_places', 'commercial_price')
    list_filter = ('building__organization', 'specialty')
    search_fields = ('specialty__name', 'building__name')
    list_editable = ('budget_places', 'commercial_places', 'commercial_price')
    fields = ('specialty', 'building', 'budget_places', 'commercial_places', 'commercial_price')
    list_per_page = 25