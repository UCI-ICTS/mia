#!/usr/bin/env python
# chatbot/models.py

from django.db import models
import uuid

class Chat(models.Model):
    chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_chat_names(cls):
        return list(cls.objects.values_list('name', flat=True))

class ChatScriptVersion(models.Model):
    chat_script_version_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='script_versions')
    version_number = models.IntegerField()
    script = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('chat', 'version_number')

    @classmethod
    def get_max_version_number(cls, chat_id):
        max_version = cls.objects.filter(chat_id=chat_id).aggregate(models.Max('version_number'))['version_number__max']
        return max_version if max_version is not None else 0
