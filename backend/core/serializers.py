from rest_framework import serializers
from django.contrib.auth import get_user_model
from chat.models import Message, Contact

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'mobile_number', 'about', 'profile_picture']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'full_name']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'sender_username']

class ContactSerializer(serializers.ModelSerializer):
    contact_user = UserSerializer(source='contact', read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'contact_user']
