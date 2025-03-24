#!/usr/bin/env python
# consentbot/apis.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from authentication.models import User, UserConsentUrl, UserFeedback
from utils.cache import get_user_workflow, set_user_workflow, set_user_consent_history, get_user_consent_history
from utils.utility_functions import (
    get_script_from_invite_id,
    get_consent_start_id,
    process_workflow,
    get_response,
    generate_workflow,
    process_test_question,
    process_user_consent,
    create_follow_up_with_user,
    clean_up_after_consent,
)


class UserInviteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Initialize or resume a consent session",
        responses={200: openapi.Response("Consent sequence", examples={
            "application/json": {
                "next_consent_sequence": {}
            }
        })},
        tags=["Consent"]
    )
    def get(self, request, invite_id):
        user_consent_history = get_user_consent_history(invite_id)
        if not user_consent_history:
            next_consent_sequence = {
                'user_responses': [('start', 'Start')],
                'user_html_type': 'button'
            }
            return Response({'next_consent_sequence': next_consent_sequence}, status=status.HTTP_200_OK)

        workflow = get_user_workflow(invite_id)
        if workflow is None:
            set_user_workflow(invite_id, [])

        return Response({'next_consent_sequence': user_consent_history}, status=status.HTTP_200_OK)


class UserResponseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Handle user response and return the next consent sequence",
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY, description="Node ID", type=openapi.TYPE_STRING)
        ],
        responses={200: openapi.Response("Next consent sequence")},
        tags=["Consent"]
    )
    def get(self, request, invite_id):
        try:
            conversation_graph = get_script_from_invite_id(invite_id)
            user_response_node_id = request.GET.get('id')

            if user_response_node_id == 'start':
                start_node_id = get_consent_start_id(conversation_graph)
                next_consent_sequence = process_workflow(start_node_id, invite_id)
                user_consent_history = get_user_consent_history(invite_id)
                user_consent_history.append({'next_consent_sequence': next_consent_sequence, 'echo_user_response': ''})
                set_user_consent_history(invite_id, user_consent_history)
                return Response({'reload': True})

            echo_user_response = get_response(conversation_graph, user_response_node_id)
            node_metadata = conversation_graph[user_response_node_id].get('metadata', {})
            next_node_id = ''

            workflow_type = node_metadata.get('workflow')
            if workflow_type == 'test_user_understanding':
                next_node_id = process_test_question(conversation_graph, user_response_node_id, invite_id)
            elif workflow_type == 'start_consent':
                next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)
            elif workflow_type == 'follow_up':
                create_follow_up_with_user(
                    invite_id,
                    node_metadata.get('follow_up_reason', ''),
                    node_metadata.get('follow_up_info', '')
                )
            elif workflow_type == 'decline_consent':
                next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)

            if not next_node_id:
                children = conversation_graph[user_response_node_id].get('child_ids', [])
                next_node_id = children[0] if children else 'terminal_node'

            next_consent_sequence = process_workflow(next_node_id, invite_id)
            set_user_consent_history(invite_id, next_consent_sequence)

            return Response({
                'echo_user_response': echo_user_response,
                'next_consent_sequence': next_consent_sequence
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateUserFeedbackAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Submit user feedback",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['satisfaction', 'suggestions'],
            properties={
                'satisfaction': openapi.Schema(type=openapi.TYPE_STRING),
                'suggestions': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={201: openapi.Response("Feedback created")},
        tags=["Feedback"]
    )
    def post(self, request, invite_id):
        user_consent_url = get_object_or_404(UserConsentUrl, consent_url=str(invite_id))
        user_id = user_consent_url.user_id

        satisfaction = request.data.get('satisfaction', '')
        suggestions = request.data.get('suggestions', '')[:2000]  # Limit text length

        UserFeedback.objects.create(
            user_id=user_id,
            satisfaction=satisfaction,
            suggestions=suggestions
        )

        return Response({'message': 'Feedback submitted successfully'}, status=status.HTTP_201_CREATED)
