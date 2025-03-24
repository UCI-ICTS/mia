#!/usr/bin/env python
# authentication/services.py

from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import User

User = get_user_model()

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

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        if not check_password(data["old_password"], user.password):
            raise serializers.ValidationError({"old_password": "Incorrect password"})

        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match"})

        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        update_last_login(None, instance)
        return instance