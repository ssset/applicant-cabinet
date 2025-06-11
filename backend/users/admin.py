# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ApplicantProfile
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser', 'consent_to_data_processing')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Устанавливаем username равным email
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'is_verified', 'is_active', 'is_staff', 'consent_to_data_processing')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('role', 'is_verified', 'consent_to_data_processing', 'organization')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser', 'consent_to_data_processing'),
        }),
    )

    add_form = CustomUserCreationForm  # Используем кастомную форму
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'date_of_birth', 'citizenship')
    search_fields = ('user__email', 'first_name', 'last_name')
    list_filter = ('citizenship', 'education_type')

# Регистрируем модели в админке
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ApplicantProfile, ApplicantProfileAdmin)