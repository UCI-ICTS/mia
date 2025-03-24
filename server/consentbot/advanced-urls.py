#!/usr/bin/env python
# consentbot/urls.py

from django.urls import path
from consentbot.apis import (
    UserInviteAPIView,
    UserResponseAPIView,
    ContactAnotherAdultAPIView,
    FamilyEnrollmentAPIView,
    ChildrenEnrollmentAPIView,
    SaveConsentPreferencesAPIView,
    # ChildAgeEnrollmentAPIView,
    # ChildConsentContactAPIView,
    UserConsentResponseAPIView,
    UserChatInviteAPIView,
    CreateUserFeedbackAPIView,
)

urlpatterns = [
    path("<uuid:invite_id>/", UserChatInviteAPIView.as_view(), name="chat_invite"),
    path("<uuid:invite_id>/user_response/", UserConsentResponseAPIView.as_view(), name="chat_response"),
    path("<uuid:invite_id>/contact_another_adult_form/", ContactAnotherAdultAPIView.as_view(), name="contact_another_adult"),
    path("<uuid:invite_id>/family_enrollment_form/", FamilyEnrollmentAPIView.as_view(), name="family_enrollment"),
    path("<uuid:invite_id>/children_enrollment_form/", ChildrenEnrollmentAPIView.as_view(), name="children_enrollment"),
    # path("<uuid:invite_id>/child_age_enrollment_form/", ChildAgeEnrollmentAPIView.as_view(), name="child_age_enrollment"),
    path("<uuid:invite_id>/save_consent_preferences/", SaveConsentPreferencesAPIView.as_view(), name="save_consent_preferences"),
    # path("<uuid:invite_id>/child_consent_contact_form/", ChildConsentContactAPIView.as_view(), name="child_consent_contact"),
    path("<uuid:invite_id>/user_feedback_form/", CreateUserFeedbackAPIView.as_view(), name="user_feedback"),
]
