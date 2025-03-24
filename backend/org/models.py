# org/models.py
from django.db import models

class Organization(models.Model):
    """
    Модель для хранения данных об организации.
    """
    name = models.CharField(max_length=100, verbose_name='Name')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Phone')
    address = models.TextField(verbose_name='Adress')
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