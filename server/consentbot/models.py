#!/usr/bin/env python
# consentbot/models.py

import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

def default_expiry():
    return timezone.now() + timedelta(weeks=2)


class ConsentAgeGroup(models.TextChoices):
    LESS_THAN_SIX = '<=6', '<=6'
    SEVEN_TO_SEVENTEEN = '7-17', '7-17'
    EIGHTEEN_AND_OVER = '>=18', '>=18'
    EIGHTEEN_AND_OVER_GUARDIANSHIP = '>=18 guardianship', '>=18 guardianship'


class Consent(models.Model):
    user_consent_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='consents')
    dependent_user = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_consents')
    consent_script = models.ForeignKey("consentbot.ConsentScript", on_delete=models.CASCADE, related_name="user_consents", null=True, blank=True)
    consent_age_group = models.CharField(max_length=20, choices=ConsentAgeGroup.choices)
    store_sample_this_study = models.BooleanField(default=True)
    store_sample_other_studies = models.BooleanField(default=False)
    store_phi_this_study = models.BooleanField(default=True)
    store_phi_other_studies = models.BooleanField(default=False)
    return_primary_results = models.BooleanField(default=False)
    return_actionable_secondary_results = models.BooleanField(default=False)
    return_secondary_results = models.BooleanField(default=False)
    consent_statements = models.TextField(default='')
    user_full_name_consent = models.CharField(max_length=200, default='')
    child_full_name_consent = models.CharField(max_length=200, null=True, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ConsentCache(models.Model):
    key = models.CharField(max_length=200, primary_key=True)
    value = models.TextField()


class ConsentScript(models.Model):
    script_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Self-reference for versioning
    derived_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )
    version_number = models.IntegerField()
    script = models.JSONField()

    class Meta:
        unique_together = ('name', 'version_number')

    def __str__(self):
        return f"{self.name} (v{self.version_number})"

    @classmethod
    def get_consent_names(cls):
        return list(cls.objects.values_list('name', flat=True))

    @classmethod
    def get_max_version_number(cls, consent_id):
        max_version = cls.objects.filter(derived_from_id=consent_id).aggregate(
            models.Max('version_number')
        )['version_number__max']
        return max_version if max_version is not None else 0


class ConsentTest(models.Model):
    user_test_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='user_tests')
    consent_script_version = models.ForeignKey(ConsentScript, on_delete=models.CASCADE, related_name='user_tests')
    test_try_num = models.IntegerField(default=1, null=True, blank=True)
    test_question = models.CharField(max_length=200)
    user_answer = models.CharField(max_length=200)
    answer_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ConsentUrl(models.Model):
    consent_url_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consent_url = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='consent_urls')
