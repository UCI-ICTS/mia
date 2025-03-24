#!/usr/bin/env python
# authentication/admin.py

"""Authentication Admin Panel
"""

from django.contrib import admin
from authentication.models import (
    User,
    UserConsentCache,
    UserConsentUrl,
    UserConsent,
    UserFeedback,
    UserFollowUp,
    UserTest
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]

@admin.register(UserConsentCache)
class UserConsentCacheAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]

@admin.register(UserConsentUrl)
class UserConsentUrlAdmin(admin.ModelAdmin):
    list_display = ["consent_url", "user", "created_at", "expires_at"]

@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ["user", "store_sample_this_study", "return_primary_results", "consented_at"]

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ["user", "satisfaction", "suggestions", "created_at"]

@admin.register(UserFollowUp)
class UserFollowUpAdmin(admin.ModelAdmin):
    list_display = ["user", "follow_up_reason", "resolved", "created_at"]

@admin.register(UserTest)
class UserTestAdmin(admin.ModelAdmin):
    list_display = ["user", "test_question", "user_answer", "answer_correct", "created_at"]

