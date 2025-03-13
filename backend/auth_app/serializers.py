from rest_framework import serializers
from users.models import CustomUser
from django.core.mail import send_mail


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    """
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }

    def validate(self, data):
        """
        Проверка совпадения паролей.
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match')

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'applicant')
        )
        # TODO: заменить на генерацию случайного кода
        verification_code = '123456'
        # Временно отключаем отправку email
        send_mail(
            subject='Verify your email',
            message=f'Your verification code: {verification_code}',
            from_email='claimov@gmail.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        return user
