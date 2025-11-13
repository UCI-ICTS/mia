#!/usr/bin/env python
# archive/apis.py

from django.contrib import admin
from django.utils.html import format_html

from archive.models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("user", "session", "file_name", "file_path", "uploaded_at")
    list_filter = ("user",)
    search_fields = ("user", "session", "file_name", "file_path", "uploaded_at")
    readonly_fields = ('download_link',)

    def download_link(self, obj):
        if obj.file_path:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file_path.url)
        return "No file"

    download_link.allow_tags = True
    download_link.short_description = "Download"