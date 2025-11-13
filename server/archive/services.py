#!/usr/bin/env python
# archive/services.py

from django.conf import settings
from django.core import signing
from rest_framework import serializers
from archive.models import Document



class DocumentInputSerializer(serializers.ModelSerializer):
    user = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = Document
        fields = ["file_name", "file_path", "user", "session", "uploaded_at"]


class DocumentOutputSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "file_name", "file_url", "user", "session", "uploaded_at"]

    def get_id(self, obj):
        return encode_id(obj.pk)

    def get_file_url(self, obj):
        request = self.context.get('request', None)
        if request and obj.file_path:
            return request.build_absolute_uri(obj.file_path.url)
        elif obj.file_path:
            return obj.file_path.url
        return None

def encode_id(pk: int) -> str:
    signer = signing.Signer(key=settings.SECRET_KEY, salt=settings.SECRET_DOC_SALT)
    return signer.sign(str(pk))

def decode_id(signed_id: str) -> int | None:
    try:
        signer = signing.Signer(key=settings.SECRET_KEY, salt=settings.SECRET_DOC_SALT)
        unsigned = signer.unsign(signed_id)
        return int(unsigned)
    except signing.BadSignature:
        return None