#!/usr/bin/env python
# authentication/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.apis import (
    get_csrf_token,
    DecoratedTokenObtainPairView,
    DecoratedTokenRefreshView,
    DecoratedTokenVerifyView,
    DecoratedTokenBlacklistView,
    FollowUpVieWSet,
    # FeedbackViewSet,
    UserViewSet,
    PasswordViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'follow-ups', FollowUpVieWSet, basename='follow_up')
router.register(r'password', PasswordViewSet, basename='password')
# router.register(r'feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path("refresh/", DecoratedTokenRefreshView.as_view()),
    path("verify/", DecoratedTokenVerifyView.as_view()),
    path("login/", DecoratedTokenObtainPairView.as_view()),
    path("logout/", DecoratedTokenBlacklistView.as_view()),
    path("csrf/", get_csrf_token),
    path('', include(router.urls)),
]
