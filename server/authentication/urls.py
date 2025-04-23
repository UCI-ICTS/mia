#!/usr/bin/env python
# authentication/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.apis import (
    get_csrf_token,
    ChangePasswordView,
    DecoratedTokenObtainPairView,
    DecoratedTokenRefreshView,
    DecoratedTokenVerifyView,
    DecoratedTokenBlacklistView,
    FollowUpVieWSet,
    # FeedbackViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'follow_ups', FollowUpVieWSet, basename='follow_up')
# router.register(r'feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path("change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("refresh/", DecoratedTokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", DecoratedTokenVerifyView.as_view(), name="token_verify"),
    path("login/", DecoratedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", DecoratedTokenBlacklistView.as_view(), name="token_blacklist"),
    path("csrf/", get_csrf_token, name="get_csrf_token"),
    path('', include(router.urls)),
]
