#!/usr/bin/env python
# authentication/apis.py

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, permissions, viewsets
from rest_framework.decorators import action
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
    FollowUpOutputSerializer,
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer,
    ActivateUserSerializer
    )
from authentication.models import FollowUp

User = get_user_model()

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"message": "CSRF cookie set"})


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
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Set temp password and mark user inactive
        temp_password = get_random_string(
            length=10,
            allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        )
        validated_data = {
            **serializer.validated_data,
            "password": temp_password,
            "is_active": False,
        }
        user = UserInputSerializer().create(validated_data)
        if user.is_staff:
            # Build token and activation URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_url = (
                f"{settings.PUBLIC_HOSTNAME}password-create?uid={uid}&token={token}"
            )

            # Email the activation link
            # Compose HTML email
            subject = "You're invited to join UCI ICTS' !"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = email

            context = {
                "activation_url": activation_url,
            }

            text_content = f"Use this link to activate your account and set your password: {activation_url}"
            html_content = render_to_string("emails/invite_email.html", context)

            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            return Response(
                {
                    "message": f"Invite sent to {email}.",
                    "user": UserOutputSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        
        return Response(
            {
                "message": f"Participant {user.username} created.",
                "user": UserOutputSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

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


    @swagger_auto_schema(
        method="post",
        request_body=UserInputSerializer,
        responses={200: "User activated and password set"},
        operation_description="Activate a user using UID and token, and set a new password.",
        tags=["Account Management"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="activate",
        permission_classes=[permissions.AllowAny],
    )
    def activate(self, request):
        serializer = ActivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid user ID"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        user.set_password(new_password)
        user.is_active = True
        user.save()

        return Response({"message": "Account activated and password set."}, status=200)


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


class PasswordViewSet(viewsets.ViewSet):
    """
    Handles requesting a reset link, confirming reset, and changing password.
    """

    permission_classes_by_action = {
        "change_password": [permissions.IsAuthenticated],
        "request_reset": [permissions.AllowAny],
        "confirm_reset": [permissions.AllowAny],
    }

    def get_permissions(self):
        return [
            permission()
            for permission in self.permission_classes_by_action.get(
                self.action, self.permission_classes
            )
        ]

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={200: "Password reset link sent"},
        operation_description="Request a password reset link by email.",
        tags=["Account Management"],
    )
    @action(detail=False, methods=["post"], url_path="reset")
    def request_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "No user found with this email"}, status=404)

        token = default_token_generator.make_token(user)
        uid = user.pk
        reset_link = f"{settings.PUBLIC_HOSTNAME}/password-reset?uid={uid}&token={token}"

        context = {"reset_link": reset_link}

        # Email content
        subject = "Reset your password – UCI ICTS' Medical Information Assistant (MIA)"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [email]
        text_content = f"Use this link to reset your password: {reset_link}"
        html_content = render_to_string("emails/password_reset_email.html", context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return Response({"message": "Password reset link sent."}, status=200)

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={200: "Password reset successful."},
        operation_description="Confirm reset with UID + token and set new password.",
        tags=["Account Management"],
    )
    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm_reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"error": "Invalid user."}, status=404)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password reset successful."}, status=200)

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: "Password changed successfully"},
        operation_description="Authenticated user can change password with old password.",
        tags=["Account Management"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="change",
        permission_classes=[permissions.IsAuthenticated],
    )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"detail": "Password changed successfully"}, status=200)

        return Response(serializer.errors, status=400)

