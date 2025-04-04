# consentbot/admin.py
from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from django import forms
from consentbot.models import (
    ConsentScript,
    ConsentCache,
    ConsentUrl,
    Consent,
    ConsentTest
) 

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

@admin.register(ConsentCache)
class ConsentCacheAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]

@admin.register(ConsentUrl)
class ConsentUrlAdmin(admin.ModelAdmin):
    list_display = ["consent_url", "user", "created_at", "expires_at"]

@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ["user", "store_sample_this_study", "return_primary_results", "consented_at"]

@admin.register(ConsentTest)
class ConsentTestAdmin(admin.ModelAdmin):
    list_display = ["user", "test_question", "user_answer", "answer_correct", "created_at"]

