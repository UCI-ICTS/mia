#!/usr/bin/env python
# authentication/admin.py

"""Authentication Admin Panel
"""

from django.contrib import admin
from authentication.models import (
    User,
    Feedback,
    FollowUp
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["user", "satisfaction", "suggestions", "created_at"]

@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ["user", "follow_up_reason", "resolved", "created_at"]
