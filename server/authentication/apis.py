#!/usr/bin/env python
# authentication/apis.py

from django.contrib.auth import login, logout
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.services import UserSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    """API for logging in"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "user": UserSerializer(user).data,
            "access": access_token,
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """API for logging out"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)
