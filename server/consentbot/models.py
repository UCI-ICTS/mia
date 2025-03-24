#!/usr/bin/env python
# consentbot/models.py

from django.db import models
import uuid

class ConsentScript(models.Model):
    consent_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
