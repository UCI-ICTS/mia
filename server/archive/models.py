#!/usr/bin/env python
# archive/models.py

from django.db import models
from authentication.models import User
from consentbot.models import ConsentSession

class Document(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='pdfs/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(ConsentSession, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)