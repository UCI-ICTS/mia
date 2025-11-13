#!/usr/bin/env python
# archive/apis.py

from django.shortcuts import render, get_object_or_404
from archive.models import Document
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from archive.services import DocumentInputSerializer, DocumentOutputSerializer, decode_id

class DocumentViewSet(viewsets.ViewSet):
    # lookup_field = 'documents'
    permission_classes = {permissions.AllowAny}

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