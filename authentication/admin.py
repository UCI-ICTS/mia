#!/usr/bin/env python
# authentication/admin.py

"""Authentication Admin Pannel
"""

from django.contrib import admin
from authentication.models import (
    User,
    UserChatCache,
    UserChatUrl,
    UserConsent,
    UserFeedback,
    UserFollowUp,
    UserTest
)

class UserAdmin(admin.ModelAdmin):
    list_display = ["email", "user_id"]

class UserChatCacheAdmin(admin.ModelAdmin):
    list_display = [""]

class UserChatUrlAdmin(admin.ModelAdmin):
    list_display = [""]

class UserConsentAdmin(admin.ModelAdmin):
    list_display = [""]

class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = [""]

class UserFollowUpAdmin(admin.ModelAdmin):
    list_display = [""]

class UserTestAdmin(admin.ModelAdmin):
    list_display = [""]


# Register your models here.
admin.site.register(User)
admin.site.register(UserChatCache)
admin.site.register(UserChatUrl)
admin.site.register(UserConsent)
admin.site.register(UserFeedback)
admin.site.register(UserFollowUp)
admin.site.register(UserTest)