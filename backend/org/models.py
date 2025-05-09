# org/models.py
from django.db import models

class Organization(models.Model):
    """
    Модель для хранения данных об организации.
    """
    name = models.CharField(max_length=100, verbose_name='Name')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Phone')
    website = models.URLField(blank=True, null=True, verbose_name='Website')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    address = models.TextField(verbose_name='Adress')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='City')
    created_at = models.DateField(auto_now=True, verbose_name='Created At')
    updated_at = models.DateField(auto_now=True, verbose_name='Updated at')

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name


class Building(models.Model):
    """
    Модель для хранения данных о корпусах учебного заведения.
    Связана с организацией, поддерживает CRUD операции для админа организации.
    """
    organization = models.ForeignKey(Organization,
                                     on_delete=models.CASCADE,
                                     related_name='buildings',
                                     verbose_name='Организация')

    name = models.CharField(max_length=100,
                            verbose_name='Название или номер корпуса',
                            help_text='Название или номер корпуса')

    address = models.CharField(max_length=200,
                               verbose_name='Адрес',
                               help_text='Полный адрес корпуса')

    phone = models.CharField(max_length=20,
                             verbose_name='Телефон',
                             help_text='Контактный телефон корпуса')

    email = models.EmailField(verbose_name='Почта', help_text='Электронная почта корпуса')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Корпус'
        verbose_name_plural = 'Корпуса'
        ordering = ['name']
        unique_together = ['organization', 'name']

    def __str__(self):
        return f'{self.name} ({self.organization.name})'


class Specialty(models.Model):
    """
    Модель для хранения данных о специальностях.
    """
    organization = models.ForeignKey(Organization,
                                     on_delete=models.CASCADE,
                                     related_name='specialties',
                                     verbose_name='Организация')
    code = models.CharField(max_length=20,
                            verbose_name='Код специальности',
                            help_text='Код специальности (например, 09.02.07)')
    name = models.CharField(max_length=200,
                            verbose_name='Название специальности',
                            help_text='Название специальности (например, Информационные системы и программирование)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    duration = models.CharField(max_length=50, blank=True, null=True, verbose_name='Срок обучения')  # Новое поле
    requirements = models.TextField(blank=True, null=True, verbose_name='Вступительные экзамены')  # Новое поле

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
        unique_together = ['organization', 'code']

    def __str__(self):
        return f'{self.code} - {self.name} ({self.organization.name})'


class BuildingSpecialty(models.Model):
    """
    Модель для связи специальности с корпусом, с указанием мест и цены.
    """
    building = models.ForeignKey(Building,
                                 on_delete=models.CASCADE,
                                 related_name='building_specialties',
                                 verbose_name='Корпус')
    specialty = models.ForeignKey(Specialty,
                                  on_delete=models.CASCADE,
                                  related_name='building_specialties',
                                  verbose_name='Специальность')
    budget_places = models.PositiveIntegerField(default=0,
                                                verbose_name='Количество бюджетных мест')
    commercial_places = models.PositiveIntegerField(default=0,
                                                    verbose_name='Количество коммерческих мест')
    commercial_price = models.DecimalField(max_digits=10,
                                           decimal_places=2,
                                           verbose_name='Цена за обучение (коммерция)',
                                           help_text='Цена за обучение на коммерческой основе')

    class Meta:
        verbose_name = 'Специальность в корпусе'
        verbose_name_plural = 'Специальности в корпусах'
        unique_together = ['building', 'specialty']

    def __str__(self):
        return f'{self.specialty.name} в {self.building.name}'