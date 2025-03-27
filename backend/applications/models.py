from django.db import models
from users.models import CustomUser
from org.models import BuildingSpecialty


class Application(models.Model):
    """
    Модель для хранения заявок абитуриентов на поступление.
    """
    applicant = models.ForeignKey(CustomUser,
                                  on_delete=models.CASCADE,
                                  related_name='applications',
                                  verbose_name='Абитуриент')
    building_specialty = models.ForeignKey(BuildingSpecialty,
                                           on_delete=models.CASCADE,
                                           related_name='applications',
                                           verbose_name='Специальность в корпусе')
    priority = models.PositiveIntegerField(default=1,
                                           verbose_name='Приоритет',
                                           help_text='Приоритет заявки (1 - самый высокий)')
    course = models.PositiveIntegerField(default=1,
                                         verbose_name='Курс',
                                         help_text='Курс (по умолчанию 1)')
    study_form = models.CharField(max_length=20,
                                  choices=[
                                      ('full_time', 'Очно'),
                                      ('part_time', 'Заочно')
                                  ],
                                  default='full_time',
                                  verbose_name='Форма обучения')
    funding_basis = models.CharField(max_length=20,
                                     choices=[
                                         ('budget', 'Бюджет'),
                                         ('commercial', 'Коммерция')
                                     ],
                                     default='budget',
                                     verbose_name='Основа обучения')
    dormitory_needed = models.BooleanField(default=False,
                                           verbose_name='Нужна ли общага')
    first_time_education = models.BooleanField(default=True,
                                               verbose_name='Образование впервые',
                                               help_text='Среднее/высшее образование впервые')
    info_source = models.CharField(max_length=200,
                                   blank=True,
                                   verbose_name='Источник информации',
                                   help_text='Источник информации о техникуме')
    status = models.CharField(max_length=20,
                              choices=[
                                  ('pending', 'На рассмотрении'),
                                  ('accepted', 'Принято'),
                                  ('rejected', 'Отклонено')
                              ],
                              default='pending',
                              verbose_name='Статус заявки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        unique_together = ['applicant', 'building_specialty']
        ordering = ['priority']

    def __str__(self):
        return f'Заявка {self.applicant.email} на {self.building_specialty.specialty.name} (Приоритет: {self.priority})'
