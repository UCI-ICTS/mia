#!/usr/bin/env python
# consentbot/admin.py

from django.contrib import admin
from .models import Consent, ConsentScriptVersion

@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(ConsentScriptVersion)
class ConsentScriptVersionAdmin(admin.ModelAdmin):
    list_display = ('consent', 'version_number', 'created_at')
    list_filter = ('consent',)
    ordering = ('consent', 'version_number')
