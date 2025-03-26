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
    UserViewSet,
    FollowUpVieWSet,
    UserConsentViewSet,
    UserConsentUrlViewSet,
    UserConsentResponseView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'follow_ups', FollowUpVieWSet, basename='follow_up')
router.register(r'consent', UserConsentViewSet, basename='consent')
router.register(r'consent-url', UserConsentUrlViewSet, basename='consent-url')

urlpatterns = [
    path("change_password/", ChangePasswordView.as_view()),
    path("refresh/", DecoratedTokenVerifyView.as_view()),
    path("verify/", DecoratedTokenRefreshView.as_view()),
    path("login/", DecoratedTokenObtainPairView.as_view()),
    path("logout/", DecoratedTokenBlacklistView.as_view()),
    path('consent-response/<uuid:invite_id>/', UserConsentResponseView.as_view(), name='consent-response'),
    path('', include(router.urls)),
    path(
        'consent-url/<str:username>/invite-link/',
        UserConsentUrlViewSet.as_view({'get': 'invite_link_by_username'}),
        name='invite-link-by-username'
    ),
]
