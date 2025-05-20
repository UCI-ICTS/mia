# consentbot/admin.py
from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from django import forms
from consentbot.models import (
    ConsentScript,
    ConsentCache,
    ConsentUrl,
    Consent,
    ConsentTestAnswer,
    ConsentTestAttempt
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

@admin.register(ConsentTestAnswer)
class ConsentTestAnswerAdmin(admin.ModelAdmin):
    list_display = ["answer_id", "question_text", "user_answer", "answer_correct", "submitted_at"]

@admin.register(ConsentTestAttempt)
class ConsentTestAttemptAdmin(admin.ModelAdmin):
    list_display = ["attempt_id", "score"]