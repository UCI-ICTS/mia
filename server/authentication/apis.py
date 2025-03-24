#!/usr/bin/env python
# authentication/apis.py

from django.db import IntegrityError
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from authentication.services import ChangePasswordSerializer

User = get_user_model()

class UserInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }

    def create(self, validated_data):
        email = validated_data.get("email")
        username = email.split("@")[0] if email else ""

        password = validated_data.pop("password", None)

        is_staff = validated_data.pop("is_staff", False)
        is_superuser = validated_data.pop("is_superuser", False)

        user = User(
            username=username,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **validated_data  # now safe to unpack
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user
    

class UserOutputSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'is_staff', 'is_superuser', 'date_joined']

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={status.HTTP_200_OK: "Password changed successfully"},
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DecoratedTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT,
                        properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                },
            )
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'].lower())
            response.data['user'] = UserOutputSerializer(user).data
        return response


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class DecoratedTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenRefreshResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyResponseSerializer(serializers.Serializer):
    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class DecoratedTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenVerifyResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedTokenBlacklistView(TokenBlacklistView):
    class TokenBlacklistResponseSerializer(serializers.Serializer):
        def create(self, validated_data):
            raise NotImplementedError()

        def update(self, instance, validated_data):
            raise NotImplementedError()
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenBlacklistResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    # permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all users",
        responses={200: UserOutputSerializer(many=True)},
        tags=["User Management"]
    )
    def list(self, request):
        """Retrieve all users (returns only safe fields)."""
        users = User.objects.all()
        serializer = UserOutputSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserInputSerializer,
        responses={201: UserOutputSerializer},
        tags=["User Management"]
    )
    def create(self, request):
        """Create a new user with password hashing."""
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(UserOutputSerializer(user).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                print(e)
                return Response(
                    {"error": "A user with this email or username already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Update an existing user",
        request_body=UserInputSerializer,
        responses={200: UserOutputSerializer},
        tags=["User Management"]
    )

    def update(self, request, username=None):
        """Update user details (hashes password if provided)."""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserInputSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserOutputSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: "User deleted"},
        tags=["User Management"]
    )
    def destroy(self, request, username=None):
        """Delete a user."""
        try:
            user = User.objects.get(username=username)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
