# consentbot/admin.py
from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from django import forms
from .models import ConsentScript

class ConsentScriptAdminForm(forms.ModelForm):
    class Meta:
        model = ConsentScript
        fields = "__all__"
        widgets = {
            "script": JSONEditorWidget(),  # 👈 This is the magic
        }

@admin.register(ConsentScript)
class ConsentScriptAdmin(admin.ModelAdmin):
    form = ConsentScriptAdminForm
    list_display = ("name", "version_number", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)
