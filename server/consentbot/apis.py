#!/usr/bin/env python
# consentbot/apis.py

import os
import json
from django.forms import ValidationError
import shortuuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
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
    ConsentSession
)
from consentbot.services import (
    ConsentInputSerializer,
    ConsentOutputSerializer,
    ConsentScriptInputSerializer,
    ConsentScriptOutputSerializer,
    ConsentResponseInputSerializer,
    ConsentSessionInputSerializer,
    ConsentSessionOutputSerializer,
    get_or_initialize_consent_history,
    get_consent_session_or_error,
    get_or_initialize_user_consent,
    handle_form_submission,
    handle_user_step
)

from consentbot.selectors import (
    get_script_from_session_slug,

)

from utils.api_helpers import (
    ConsentResponseSchema,
    consent_response_constructor
)

User = get_user_model()

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Load or initialize a consent session using session slug",
        responses={200: ConsentResponseSchema},
        tags=["User Consent"]
    )
    def retrieve(self, request, pk=None):
        session_slug = pk
        try:
            # Get session (fallback to .get for internal control)
            session = get_consent_session_or_error(session_slug)

            # Get or create consent + chat history
            consent, created = get_or_initialize_user_consent(session_slug)
            history, _ = get_or_initialize_consent_history(session_slug)

            return consent_response_constructor(
                status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
                status_label="ok",
                session=ConsentSessionOutputSerializer(session).data,
                consent=ConsentOutputSerializer(consent).data,
                chat=history,
                render=None,
                error=None
            )

        except Exception as error:
            return consent_response_constructor(
                status_code=status.HTTP_400_BAD_REQUEST,
                status_label="error",
                session=None,
                consent=None,
                chat=[],
                render=None,
                error=str(error)
            )

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


class ConsentSessionViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    permission_classes = {permissions.IsAuthenticated}
    
    @swagger_auto_schema(
        operation_description="Retrieve the latest consent URL for a user by username",
        responses={200: ConsentSessionOutputSerializer},
        tags=["Consent URLs"]
    )
    
    def invite_link_by_username(self, request, username=None):
        user = get_object_or_404(User, username=username)
        invite = user.consent_sessions.order_by('-created_at').first()

        if not invite:
            return Response({"detail": "No invite link found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConsentSessionOutputSerializer(invite)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        operation_description="Create a consent URL",
        request_body=ConsentSessionInputSerializer,
        responses={200: UserOutputSerializer(many=True)},
        tags=["Consent URLs"]
    )
    def create(self, request):
        """Create the consent object"""
        serializer = ConsentSessionInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                consent = serializer.save()
                # Email the activation link
                # Compose HTML email
                subject = "You're invited to join UCI ICTS' Medical Information Assistant (MIA)!"
                from_email = settings.DEFAULT_FROM_EMAIL
                user = User.objects.get(pk=consent.user_id)
                to_email = user.email
                session_slug = f"{settings.PUBLIC_HOSTNAME}/consent/{consent.session_slug}"
                context = {
                    "session_slug": session_slug,
                }

                text_content = f"Use this link to access the chat: {session_slug}"
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
                # return Response(ConsentSessionOutputSerializer(consent).data, status=status.HTTP_200_OK)
            except IntegrityError as error:
                return Response(data=str(error), status=status.HTTP_400_BAD_REQUEST)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsentResponseViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve the next part of the consent chat based on a node_id and session_slug.",
        query_serializer=ConsentResponseInputSerializer,
        tags=["Consent Response"]
    )
    def retrieve(self, request, pk=None):
        try:
            # Validate request
            serializer = ConsentResponseInputSerializer(
                data={"session_slug": pk, "node_id": request.query_params.get("node_id")},
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Resolve session
            session_slug = str(data["session_slug"])
            node_id = data["node_id"]
            try:
                session = ConsentSession.objects.get(session_slug=session_slug)
            except ConsentSession.DoesNotExist:
                raise ValueError(f"No session found for slug: {session_slug}")

            # Load graph + consent
            graph = get_script_from_session_slug(session_slug)
            chat= handle_user_step(session_slug, node_id, graph)

            consent, created = get_or_initialize_user_consent(session_slug)

            return consent_response_constructor(
                status_code=status.HTTP_200_OK,
                status_label="ok",
                session=ConsentSessionOutputSerializer(session).data,
                consent=ConsentOutputSerializer(consent).data,
                chat=chat,
                render=chat[-1]['render']
            )

        except Exception as error:
            return consent_response_constructor(
                status_code=status.HTTP_400_BAD_REQUEST,
                status_label="error",
                session=None,
                consent=None,
                chat=[],
                render=None,
                error=str(error)
            )


    @swagger_auto_schema(
        operation_description="Submit a form response during the consent chat.",
        request_body=ConsentResponseInputSerializer,
        tags=["Consent Response"]
    )
    def create(self, request):
        try:
            serializer = ConsentResponseInputSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            session = get_consent_session_or_error(data["session_slug"])
            consent, _ = get_or_initialize_user_consent(data["session_slug"])

            history, render = handle_form_submission(data)
            return consent_response_constructor(
                status_code=status.HTTP_200_OK,
                status_label="ok",
                session=ConsentSessionOutputSerializer(session).data,
                consent=ConsentOutputSerializer(consent).data,
                chat=history,
                render=render
            )

        except Exception as e:
            return consent_response_constructor(
                status_code=status.HTTP_400_BAD_REQUEST,
                status_label="error",
                session=None,
                consent=None,
                chat=[],
                render=None,
                error=str(e)
            )
