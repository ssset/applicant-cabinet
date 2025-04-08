from django.db import models
from users.models import CustomUser
from org.models import Organization


class Chat(models.Model):
    """
    Модель чата, привязанного к организации.
    """
    organization = models.ForeignKey(Organization,
                                     on_delete=models.CASCADE,
                                     related_name='chats',
                                     verbose_name='Организация')
    applicant = models.ForeignKey(CustomUser,
                                  on_delete=models.CASCADE,
                                  related_name='chats',
                                  verbose_name='Абитуриент')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        unique_together = ['organization', 'applicant']

    def __str__(self):
        return f'Чат {self.applicant.email} с {self.organization.name}'


class Message(models.Model):
    """
    Модель сообщения в чате.
    """
    chat = models.ForeignKey(Chat,
                             on_delete=models.CASCADE,
                             related_name='messages',
                             verbose_name='Чат')
    sender = models.ForeignKey(CustomUser,
                               on_delete=models.CASCADE,
                               related_name='sent_messages',
                               verbose_name='Отправитель')
    content = models.TextField(verbose_name='Содержание сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'Сообщение от {self.sender.email} в чате {self.chat.id}'
