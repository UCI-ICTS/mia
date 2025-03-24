#!/usr/bin/env python
# consentbot/urls.py

from django.urls import path
from consentbot.apis import (
    UserInviteAPIView,
    UserResponseAPIView,
    CreateUserFeedbackAPIView,
)

urlpatterns = [
    path('invite/<uuid:invite_id>/', UserInviteAPIView.as_view(), name='user-invite'),
    path('invite/<uuid:invite_id>/response/', UserResponseAPIView.as_view(), name='user-response'),
    path('invite/<uuid:invite_id>/feedback/', CreateUserFeedbackAPIView.as_view(), name='user-feedback'),
]
