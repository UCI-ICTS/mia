#!/usr/bin/env python
# authentication/services.py

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import User

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="user_id", read_only=True)  # Map `id` to `user_id`

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user"""
        email = data.get("email").lower()
        password = data.get("password")
        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password")

        data["user"] = user
        return data
