#!/usr/bin/env python
# administration/apps.py

from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "administration"
