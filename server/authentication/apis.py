#!/usr/bin/env python
# authentication/apis.py

from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, permissions, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.views import APIView

from authentication.services import (
    ChangePasswordSerializer,
    UserInputSerializer,
    UserOutputSerializer,
    FollowUpInputSerializer,
    FollowUpOutputSerializer
    )
from authentication.models import FollowUp

User = get_user_model()

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"message": "CSRF cookie set"})

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


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    # permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all users",
        responses={200: UserOutputSerializer(many=True)},
        tags=["Account Management"]
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
        tags=["Account Management"]
    )
    def create(self, request):
        """Create a new user with password hashing."""

        serializer = UserInputSerializer(data=request.data, context={'request': request})
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
        tags=["Account Management"]
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
        tags=["Account Management"]
    )
    def destroy(self, request, username=None):
        """Delete a user."""
        try:
            user = User.objects.get(username=username)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class FollowUpVieWSet(viewsets.ViewSet):
    # permission_classes = {permissions.IsAuthenticated}
    permission_classes = {permissions.AllowAny}
    # def get_permissions(self):
    #     if self.action == 'create':
    #         return [permissions.AllowAny()]
    #     return [permissions.IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_description="Retrieve all follow ups",
        # responses={200: UserOutputSerializer(many=True)},
        tags=["Follow Ups"]
    )

    def list(slef, request):
        """Retrieve all Follow up instances
        """
        follow_ups = FollowUp.objects.all()
        serializer = FollowUpOutputSerializer(follow_ups, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Create a new follow-up entry",
        request_body=FollowUpInputSerializer,
        responses={201: FollowUpOutputSerializer()},
        tags=["Follow Ups"]
    )
    def create(self, request):
        serializer = FollowUpInputSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            output = FollowUpOutputSerializer(instance)
            return Response(output.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


