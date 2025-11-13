#!/usr/bin/env python
# archive/apis.py

from django.shortcuts import render, get_object_or_404
from archive.models import Document
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from archive.services import (
    DocumentEmaiSerializer,
    DocumentInputSerializer,
    DocumentOutputSerializer,
    decode_id
)
from utils.email_helpers import send_html_email

class DocumentViewSet(viewsets.ViewSet):
    permission_classes = {permissions.IsAuthenticated}

    @swagger_auto_schema(
        operation_description="Send user document record",
        request_body=DocumentEmaiSerializer,
        responses={200: DocumentOutputSerializer(many=True)},
        tags=["User Documents"]
    )
    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        serializer = DocumentEmaiSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        real_pk = decode_id(pk)
        if real_pk is None:
            return Response({"detail": "Invalid document ID"}, status=status.HTTP_404_NOT_FOUND)
        
        email = serializer.validated_data["email"]
        custom_message = serializer.validated_data.get("message", "")

        document = get_object_or_404(Document, pk=real_pk)
        
        # Email context for the template
        context = {
            "document": document,
            "message": custom_message,
            "user": document.user,
            "session": document.session,
        }

        # Prepare attachment
        attachments = []
        if document.file_path:
            with open(document.file_path.path, "rb") as f:
                attachments.append((
                    document.file_name,
                    f.read(),
                    "application/pdf"
                ))

        send_html_email(
            subject=f"Requested Document: {document.file_name}",
            to_email=email,
            template_name="emails/consentbot_document_email.html",  # You must create this
            context=context,
            attachments=attachments,
        )

        return Response({"detail": "Email sent"}, status=status.HTTP_200_OK)
        
    @swagger_auto_schema(
        operation_description="List all user document records",
        responses={200: DocumentOutputSerializer(many=True)},
        tags=["User Documents"]
    )
    def list(self, request):
        queryset = Document.objects.all()
        serializer = DocumentOutputSerializer(queryset, context={"request": request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Retrieve a document by ID",
        responses={200: DocumentOutputSerializer()},
        tags=["User Documents"]
    )
    def retrieve(self, request, pk=None):
        real_pk = decode_id(pk)
        if real_pk is None:
            return Response({"detail": "Invalid or expired document ID"}, status=400)
        document = get_object_or_404(Document, pk=real_pk)

        serializer = DocumentOutputSerializer(document, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Upload a new document",
        request_body=DocumentInputSerializer,
        responses={201: DocumentOutputSerializer()},
        tags=["User Documents"]
    )
    def create(self, request):
        serializer = DocumentInputSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            output = DocumentOutputSerializer(document, context={"request": request})
            return Response(output.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a document by ID",
        tags=["User Documents"]
    )
    def destroy(self, request, pk=None):
        real_pk = decode_id(pk)
        if real_pk is None:
            return Response({"detail": "Invalid or expired document ID"}, status=400)
        document = get_object_or_404(Document, pk=real_pk)

        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)