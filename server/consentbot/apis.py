#!/usr/bin/env python
# consentbot/apis.py

import os
import json
import shortuuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from authentication.services import (
    UserOutputSerializer,
    create_follow_up_with_user
)
from consentbot.models import (
    Consent,
    ConsentScript,
    ConsentUrl
)
from consentbot.services import (
    ConsentInputSerializer,
    ConsentOutputSerializer,
    ConsentScriptInputSerializer,
    ConsentScriptOutputSerializer,
    ConsentResponseInputSerializer,
    ConsentUrlInputSerializer,
    ConsentUrlOutputSerializer,
    get_or_initialize_consent_history,
    get_or_initialize_user_consent,
    process_consent_sequence,
    format_turn,
    handle_family_enrollment_form,
    handle_consent,
    handle_phi_use,
    handle_result_return,
    handle_sample_storage,
    handle_user_feedback_form,
    handle_other_adult_contact_form,
    process_test_question,
    process_user_consent
)

from consentbot.selectors import (
    get_script_from_invite_id,
    get_consent_start_id,
    get_user_consent_history,
    get_user_label,

)
from utils.cache import set_user_consent_history

User = get_user_model()
FORM_HANDLER_MAP = {
    "family_enrollment": handle_family_enrollment_form,
    "checkbox_form": handle_family_enrollment_form,
    "sample_storage": handle_sample_storage,
    "phi_use": handle_phi_use,
    "result_return": handle_result_return,
    "feedback": handle_user_feedback_form,
    "consent": handle_consent,
    "text_fields": handle_other_adult_contact_form,
    # "child_contact": handle_child_contact_form,
}

class ConsentScriptViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all consent scripts", 
        tags=["Consent Scripts"],
        responses={200: ConsentScriptOutputSerializer(many=True)}
    )
    def list(self, request):
        scripts = ConsentScript.objects.all()
        serializer = ConsentScriptOutputSerializer(scripts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get consent script details",
        tags=["Consent Scripts"],
        responses={200: ConsentScriptOutputSerializer}
    )
    def retrieve(self, request, pk=None):
        script = get_object_or_404(ConsentScript, pk=pk)
        serializer = ConsentScriptOutputSerializer(script)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create consent script",
        tags=["Consent Scripts"],
        request_body=ConsentScriptInputSerializer,
        responses={201: ConsentScriptOutputSerializer}
    )
    def create(self, request):
        serializer = ConsentScriptInputSerializer(data=request.data)
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

        output_serializer = ConsentScriptOutputSerializer(new_script)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        operation_description="Create consent script",
        tags=["Consent Scripts"],
        request_body=ConsentScriptInputSerializer,
        responses={201: ConsentScriptOutputSerializer}
    )
    def update(self, request, pk=None):
        """Update consent script metadata"""
        try:
            script = get_object_or_404(ConsentScript, pk=pk)
        except ConsentScript.DoesNotExist:
            return Response({"detail": "Consent script not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConsentInputSerializer(script, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(ConsentScriptOutputSerializer(script).data)
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
            "render_type": 'button',
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


class ConsentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="List all user consent records",
        responses={200: ConsentOutputSerializer(many=True)},
        tags=["User Consent"]
    )
    def list(self, request):
        queryset = Consent.objects.all()
        serializer = ConsentOutputSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Load or initialize a consent session using invite UUID",
        responses={200: ConsentOutputSerializer},
        tags=["User Consent"]
    )
    def retrieve(self, request, pk=None):
        consent, created = get_or_initialize_user_consent(pk)
        history, just_created = get_or_initialize_consent_history(pk)
        response_data = ConsentOutputSerializer(consent).data
        response_data["chat"] = history

        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="Create a new user consent record",
        request_body=ConsentInputSerializer,
        responses={201: ConsentOutputSerializer},
        tags=["User Consent"]
    )
    def create(self, request):
        serializer = ConsentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(ConsentOutputSerializer(instance).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update a user consent record",
        request_body=ConsentInputSerializer,
        responses={200: ConsentOutputSerializer},
        tags=["User Consent"]
    )
    def update(self, request, pk=None):
        instance = get_object_or_404(Consent, pk=pk)
        serializer = ConsentInputSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(ConsentOutputSerializer(updated).data)

    @swagger_auto_schema(
        operation_description="Delete a user consent record",
        tags=["User Consent"]
    )
    def destroy(self, request, pk=None):
        instance = get_object_or_404(Consent, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConsentUrlViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    permission_classes = {permissions.IsAuthenticated}
    
    @swagger_auto_schema(
        operation_description="Retrieve the latest consent URL for a user by username",
        responses={200: ConsentUrlOutputSerializer},
        tags=["Consent URLs"]
    )
    
    def invite_link_by_username(self, request, username=None):
        user = get_object_or_404(User, username=username)
        invite = user.consent_urls.order_by('-created_at').first()

        if not invite:
            return Response({"detail": "No invite link found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConsentUrlOutputSerializer(invite)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        operation_description="Create a consent URL",
        responses={200: UserOutputSerializer(many=True)},
        tags=["Consent URLs"]
    )
    def create(self, request):
        """Create the consent object"""
        serializer = ConsentUrlInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                consent = serializer.save()
                # import pdb; pdb.set_trace()
                # Email the activation link
                # Compose HTML email
                subject = "You're invited to join UCI ICTS' Medical Information Assistant (MIA)!"
                from_email = settings.DEFAULT_FROM_EMAIL
                user = User.objects.get(pk=consent.user_id)
                to_email = user.email
                consent_url = f"{settings.PUBLIC_HOSTNAME}/consent/{consent.consent_url}"
                context = {
                    "consent_url": consent_url,
                }

                text_content = f"Use this link to access the chat: {consent_url}"
                html_content = render_to_string("emails/consent_invite.html", context)

                msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                return Response(
                    {
                        "message": f"Invite sent to {to_email}.",
                        "user": UserOutputSerializer(user).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
                # return Response(ConsentUrlOutputSerializer(consent).data, status=status.HTTP_200_OK)
            except:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsentResponseViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve the next part of the consent chat based on a node_id and invite_id.",
        query_serializer=ConsentResponseInputSerializer,
        tags=["Consent Response"]
    )
    def retrieve(self, request, pk=None):
        serializer = ConsentResponseInputSerializer(
            data={"invite_id": pk, "node_id": request.query_params.get("node_id")},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invite_id = str(data["invite_id"])
        node_id = data["node_id"]
        graph = get_script_from_invite_id(invite_id)
        history = get_user_consent_history(invite_id)

        try:
            if node_id == "start":
                return self._handle_start(invite_id, graph, history)

            return self._handle_next(invite_id, node_id, graph, history)

        except Exception as e:
            return Response({
                "chat": [],
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def _handle_start(self, invite_id, graph, history):
        start_node_id = get_consent_start_id(graph)
        first_sequence = process_consent_sequence(start_node_id, invite_id)
        history.append(format_turn(graph, "start", "", first_sequence))
        set_user_consent_history(invite_id, history)
        return Response({
            "chat": history,
            "next_node_id": start_node_id,
            "end_sequence": first_sequence.get("end_sequence", False),
        })

    def _handle_next(self, invite_id, node_id, graph, history):
        node = graph.get(node_id, {})
        metadata = graph[node_id].get("metadata", {})
        workflow = metadata.get("workflow", "")
        echo_user_response = get_user_label(node) if node.get("type") == "user" else ""
        next_node_id = ""
        
        if workflow == "test_user_understanding":
            next_node_id = process_test_question(graph, node_id, invite_id)
        elif workflow in ["start_consent", "decline_consent"]:
            next_node_id = process_user_consent(graph, node_id, invite_id)
        elif workflow == "follow_up":
            create_follow_up_with_user(
                invite_id,
                metadata.get("follow_up_reason", ""),
                metadata.get("follow_up_info", "")
            )

        if not next_node_id:
            next_node_id = graph[node_id].get("child_ids", [None])[0]

        next_sequence = process_consent_sequence(next_node_id, invite_id)
        history.append(format_turn(graph, node_id, echo_user_response, next_sequence))
        set_user_consent_history(invite_id, history)

        return Response({
            "chat": history,
            "next_node_id": next_node_id,
            "end_sequence": next_sequence.get("end_sequence", False),
        })

    @swagger_auto_schema(
        operation_description="Submit a form response during the consent chat.",
        request_body=ConsentResponseInputSerializer,
        tags=["Consent Response"]
    )
    def create(self, request):

        serializer = ConsentResponseInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            return self._handle_form_submission(data)

        except Exception as e:
            return Response({
                "chat": [],
                "status": "error",
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

    def _handle_form_submission(self, data):
        invite_id = str(data["invite_id"])
        form_type = data["form_type"]
        responses = data["form_responses"] + [{"name": "node_id", "value": data["node_id"]}]
        graph = get_script_from_invite_id(invite_id)

        handler = FORM_HANDLER_MAP.get(form_type)
        if not handler:
            raise ValueError(f"Unknown form_type: {form_type}")

        result = handler(graph, invite_id, responses)
        return Response({
            "chat": result,
            "next_node_id": result[-1].get("node_id"),
            "end_sequence": result[-1].get("end_sequence", False),
        })

