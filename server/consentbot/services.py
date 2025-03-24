#!/usr/bin/env python
# consentbot/serializers.py

from rest_framework import serializers
from consentbot.models import ConsentScript

class ConsentInputSerializer(serializers.ModelSerializer):
    derived_from = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = ConsentScript
        fields = ['name', 'description', 'derived_from']

class ConsentOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentScript
        fields = ['consent_id', 'name', 'description', 'version_number', 'script', 'created_at']

