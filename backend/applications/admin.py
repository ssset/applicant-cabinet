# applications/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Поля для отображения в списке заявлений
    list_display = (
        'applicant_email', 'specialty_name', 'building_name', 'organization_name',
        'priority', 'course', 'study_form', 'funding_basis', 'status', 'created_at', 'status_colored',
    )

    # Фильтры для списка
    list_filter = (
        'status', 'study_form', 'funding_basis', 'dormitory_needed', 'first_time_education',
        'created_at', 'building_specialty__specialty', 'building_specialty__building',
        'building_specialty__building__organization',
    )

    # Поля для поиска
    search_fields = (
        'applicant__email', 'building_specialty__specialty__name',
        'building_specialty__building__name', 'building_specialty__building__organization__name',
    )

    # Поля, редактируемые прямо в списке
    list_editable = ('status', 'priority')

    # Количество записей на странице
    list_per_page = 20

    # Поля в форме редактирования
    fields = (
        'applicant', 'building_specialty', 'priority', 'course', 'study_form',
        'funding_basis', 'dormitory_needed', 'first_time_education', 'info_source',
        'status', 'reject_reason', 'created_at', 'updated_at',
    )

    # Поля только для чтения
    readonly_fields = ('created_at', 'updated_at', 'applicant')

    # Массовые действия
    actions = ['mark_as_accepted', 'mark_as_rejected', 'mark_as_pending']

    # Кастомные методы для отображения
    def applicant_email(self, obj):
        """Отображение email абитуриента с ссылкой на профиль."""
        url = reverse('admin:users_customuser_change', args=[obj.applicant.id])
        return format_html('<a href="{}">{}</a>', url, obj.applicant.email)

    applicant_email.short_description = 'Абитуриент'

    def specialty_name(self, obj):
        """Отображение названия специальности."""
        return obj.building_specialty.specialty.name if obj.building_specialty else 'Не указано'

    specialty_name.short_description = 'Специальность'

    def building_name(self, obj):
        """Отображение названия корпуса."""
        return obj.building_specialty.building.name if obj.building_specialty else 'Не указано'

    building_name.short_description = 'Корпус'

    def organization_name(self, obj):
        """Отображение названия организации."""
        return (obj.building_specialty.building.organization.name
                if obj.building_specialty and obj.building_specialty.building else 'Не указано')

    organization_name.short_description = 'Организация'

    def status_colored(self, obj):
        """Отображение статуса с цветовым выделением."""
        colors = {
            'pending': 'orange',
            'accepted': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}">{}</span>', color, obj.get_status_display())

    status_colored.short_description = 'Статус (цветной)'

    # Массовые действия
    @admin.action(description='Пометить как принятые')
    def mark_as_accepted(self, request, queryset):
        updated = queryset.update(status='accepted', reject_reason='')
        self.message_user(request, f'Успешно принято {updated} заявок.')

    @admin.action(description='Пометить как отклоненные')
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected', reject_reason='Отклонено администратором')
        self.message_user(request, f'Успешно отклонено {updated} заявок.')

    @admin.action(description='Пометить как на рассмотрении')
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending', reject_reason='')
        self.message_user(request, f'Успешно установлено "На рассмотрении" для {updated} заявок.')

    # Логика для формы редактирования
    def get_readonly_fields(self, request, obj=None):
        """Поле reject_reason редактируется только при статусе 'rejected'."""
        if obj and obj.status != 'rejected':
            return self.readonly_fields + ('reject_reason',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Очистка reject_reason, если статус не 'rejected'."""
        if obj.status != 'rejected':
            obj.reject_reason = ''
        super().save_model(request, obj, form, change)


# Настройка отображения названия в админке
ApplicationAdmin.verbose_name = 'Заявка'
ApplicationAdmin.verbose_name_plural = 'Заявки'