from rest_framework import serializers
from .models import Chat, Message
from users.models import CustomUser
from org.models import Organization

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role']

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_email', 'sender_role', 'content', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    applicant_email = serializers.CharField(source='applicant.email', read_only=True)
    organization = OrganizationSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'applicant', 'applicant_email', 'organization', 'organization_name', 'messages', 'created_at', 'updated_at']