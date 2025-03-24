#!/usr/bin/env python
# consentbot/models.py

from django.db import models
import uuid

class Consent(models.Model):
    consent_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_consent_names(cls):
        return list(cls.objects.values_list('name', flat=True))

class ConsentScriptVersion(models.Model):
    consent_script_version_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consent = models.ForeignKey(Consent, on_delete=models.CASCADE, related_name='script_versions')
    version_number = models.IntegerField()
    script = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('consent', 'version_number')

    @classmethod
    def get_max_version_number(cls, consent_id):
        max_version = cls.objects.filter(consent_id=consent_id).aggregate(models.Max('version_number'))['version_number__max']
        return max_version if max_version is not None else 0
