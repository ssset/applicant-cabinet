
# auth/serializers.py
from rest_framework import serializers
from users.models import CustomUser
from django.conf import settings
from django.template.loader import render_to_string
from applicant.tasks import send_email_task

class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    """
    password2 = serializers.CharField(write_only=True, required=False, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'password', 'password2', 'role', 'consent_to_data_processing']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }

    def validate(self, data):
        if 'password2' in data and data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match')
        if not self.partial and not data.get('consent_to_data_processing', False):
            raise serializers.ValidationError('You must consent to data processing')
        return data

    def create(self, validated_data):
        validated_data.pop('password2', None)  # Удаляем password2, если оно есть
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'applicant'),
            consent_to_data_processing=validated_data['consent_to_data_processing']
        )
        # Формируем ссылку для верификации
        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email/?token={user.verification_token}"
        )

        # Рендерим HTML-шаблон
        email_context = {
            'logo_url': 'http://localhost:5173/static/logo.png',  # Замени на реальный URL логотипа
            'verify_url': verification_link,
            'support_url': 'http://localhost:5173/support',  # Замени на реальный URL поддержки
            'year': 2025,
        }
        email_html = render_to_string('email/verification_email.html', email_context)

        # Асинхронно отправляем письмо через Celery
        send_email_task.delay(
            subject='Подтверждение Email',
            message=(
                f'Пожалуйста, подтвердите ваш email, перейдя по ссылке: {verification_link}\n\n'
                f'После подтверждения вы будете перенаправлены на страницу входа.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=email_html,
        )
        return user
