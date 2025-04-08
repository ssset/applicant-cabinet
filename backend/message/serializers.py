from rest_framework import serializers
from .models import Chat, Message
from users.models import CustomUser
from org.models import Organization

class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сообщений в чате.
    """
    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_email', 'content', 'created_at']
        extra_kwargs = {
            'sender': {'read_only': True}
        }

class ChatSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чатов.
    """
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'applicant', 'applicant_email', 'organization', 'organization_name', 'messages', 'created_at', 'updated_at']
        extra_kwargs = {
            'applicant': {'read_only': True},
            'organization': {'read_only': True}
        }
        