#!/usr/bin/env python
# consentbot/apis.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings
import os
import json
from datetime import datetime
import shortuuid

from consentbot.models import ConsentScript
from consentbot.services import ConsentInputSerializer, ConsentOutputSerializer

class ConsentScriptViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all consent scripts", 
        tags=["Consent Scripts"],
        responses={200: ConsentOutputSerializer(many=True)}
    )
    def list(self, request):
        scripts = ConsentScript.objects.all()
        serializer = ConsentOutputSerializer(scripts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get consent script details",
        tags=["Consent Scripts"],
        responses={200: ConsentOutputSerializer}
    )
    def retrieve(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        serializer = ConsentOutputSerializer(script)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create consent script",
        tags=["Consent Scripts"],
        request_body=ConsentInputSerializer,
        responses={201: ConsentOutputSerializer}
    )
    def create(self, request):
        serializer = ConsentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        base_script_id = serializer.validated_data.get('derived_from')
        base_script = ConsentScript.objects.filter(consent_id=base_script_id).first() if base_script_id else None

        new_script = ConsentScript.objects.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description'],
            script={},
            derived_from=base_script,
            version_number=(ConsentScript.get_max_version_number(base_script_id) + 1 if base_script else 0)
        )

        output_serializer = ConsentOutputSerializer(new_script)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        operation_description="Create consent script",
        tags=["Consent Scripts"],
        request_body=ConsentInputSerializer,
        responses={201: ConsentOutputSerializer}
    )
    def update(self, request, pk=None):
        """Update consent script metadata"""
        try:
            script = get_object_or_404(ConsentScript, pk=pk)
        except ConsentScript.DoesNotExist:
            return Response({"detail": "Consent script not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConsentInputSerializer(script, data=request.data, partial=True)
        import pdb; pdb.set_trace()
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(ConsentOutputSerializer(script).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    @swagger_auto_schema(
        operation_description="Delete consent script",
        tags=["Consent Scripts"]
    )
    def destroy(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        script.delete()
        return Response({"message": "Consent script deleted"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="download", url_name="download")
    def download_script(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{script.name}_{timestamp}.json"
        temp_path = os.path.join(settings.BASE_DIR, 'temp_scripts', filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        with open(temp_path, 'w') as f:
            json.dump(script.script, f, indent=4)

        return FileResponse(open(temp_path, 'rb'), as_attachment=True, filename=filename)

    @action(detail=True, methods=["post"], url_path="upload", url_name="upload")
    def upload_script(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        data = json.loads(request.body)
        new_script = json.loads(data['script'])
        script.script = new_script
        script.save()
        return Response({"message": "Script uploaded successfully."})

    @action(detail=True, methods=["post"], url_path="add-message", url_name="add-message")
    def add_message(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        versioned_script = script.script

        new_id = shortuuid.uuid()[:7]
        while new_id in versioned_script:
            new_id = shortuuid.uuid()[:7]

        messages = [m.strip() for m in request.data.get('messages', '').split('\n')]
        parent_ids = [p.strip() for p in request.data.get('parent_ids', '').split(',')]
        new_message = {
            "type": request.data.get('type'),
            "messages": messages,
            "parent_ids": parent_ids,
            "child_ids": [],
            "attachment": None,
            "html_type": 'button',
            "html_content": None,
            "metadata": {
                'workflow': '',
                'end_sequence': False
            }
        }
        versioned_script[new_id] = new_message

        for parent_id in parent_ids:
            if parent_id in versioned_script:
                versioned_script[parent_id]['child_ids'].append(new_id)

        script.script = versioned_script
        script.save()

        return Response({
            "id": new_id,
            "type": new_message["type"],
            "messages": new_message["messages"],
            "parent_ids": new_message["parent_ids"]
        })
