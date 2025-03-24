#!/usr/bin/env python
# authentication/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.apis import (
    ChangePasswordView,
    DecoratedTokenObtainPairView,
    DecoratedTokenRefreshView,
    DecoratedTokenVerifyView,
    DecoratedTokenBlacklistView,
    UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path("change_password/", ChangePasswordView.as_view()),
    path("refresh/", DecoratedTokenVerifyView.as_view()),
    path("verify/", DecoratedTokenRefreshView.as_view()),
    path("login/", DecoratedTokenObtainPairView.as_view()),
    path("logout/", DecoratedTokenBlacklistView.as_view()),
    path('', include(router.urls)),
]
