# auth/serializers.py
from rest_framework import serializers
from users.models import CustomUser
from django.core.mail import send_mail


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    """
    password2 = serializers.CharField(write_only=True, required=False, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['id','email', 'password', 'password2', 'role', 'consent_to_data_processing']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }

    def validate(self, data):
        # Проверяем совпадение паролей только если password2 предоставлен
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
        send_mail(
            subject='Verify your email',
            message=f'Your verification code: {user.verification_code}',
            from_email='claimov@gmail.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        return user
