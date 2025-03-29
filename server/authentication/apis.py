#!/usr/bin/env python
# authentication/apis.py

from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, permissions, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.views import APIView

from authentication.models import (
    UserFollowUp,
    UserConsentUrl,
    UserConsent,
    ConsentAgeGroup
)
from authentication.services import (
    ChangePasswordSerializer,
    UserInputSerializer,
    UserOutputSerializer,
    UserConsentInputSerializer, 
    UserConsentOutputSerializer,
    UserUserFollowUpInputSerializer,
    UserUserFollowUpOutputSerializer,
    UserConsentUrlInputSerializer,
    UserConsentUrlOutputSerializer,
    UserConsentResponseInputSerializer,
    UserConsentResponseOutputSerializer,
    retrieve_or_initialize_user_consent,
    )

from authentication.selectors import get_or_initialize_consent_history

from utils.utility_functions import (
    get_script_from_invite_id,
    get_consent_start_id,
    process_workflow,
    get_response,
    process_test_question,
    process_user_consent,
    create_follow_up_with_user,
    handle_family_enrollment_form,
)
from utils.cache import (get_user_consent_history, set_user_consent_history)
User = get_user_model()


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={status.HTTP_200_OK: "Password changed successfully"},
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DecoratedTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT,
                        properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                },
            )
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'].lower())
            response.data['user'] = UserOutputSerializer(user).data
        return response


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class DecoratedTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenRefreshResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyResponseSerializer(serializers.Serializer):
    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class DecoratedTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenVerifyResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedTokenBlacklistView(TokenBlacklistView):
    class TokenBlacklistResponseSerializer(serializers.Serializer):
        def create(self, validated_data):
            raise NotImplementedError()

        def update(self, instance, validated_data):
            raise NotImplementedError()
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenBlacklistResponseSerializer,
        },
        tags=["Account Management"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    # permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all users",
        responses={200: UserOutputSerializer(many=True)},
        tags=["User Management"]
    )
    def list(self, request):
        """Retrieve all users (returns only safe fields)."""
        users = User.objects.all()
        serializer = UserOutputSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserInputSerializer,
        responses={201: UserOutputSerializer},
        tags=["User Management"]
    )
    def create(self, request):
        """Create a new user with password hashing."""
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(UserOutputSerializer(user).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                print(e)
                return Response(
                    {"error": "A user with this email or username already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Update an existing user",
        request_body=UserInputSerializer,
        responses={200: UserOutputSerializer},
        tags=["User Management"]
    )

    def update(self, request, username=None):
        """Update user details (hashes password if provided)."""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserInputSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserOutputSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: "User deleted"},
        tags=["User Management"]
    )
    def destroy(self, request, username=None):
        """Delete a user."""
        try:
            user = User.objects.get(username=username)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class FollowUpVieWSet(viewsets.ViewSet):
    # permission_classes = {permissions.IsAuthenticated}
    permission_classes = {permissions.AllowAny}
    # def get_permissions(self):
    #     if self.action == 'create':
    #         return [permissions.AllowAny()]
    #     return [permissions.IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_description="Retrieve all follow ups",
        responses={200: UserOutputSerializer(many=True)},
        tags=["Follow Ups"]
    )

    def list(slef, request):
        """Retrieve all Follow up instances
        """
        follow_ups = UserFollowUp.objects.all()
        serializer = UserUserFollowUpOutputSerializer(follow_ups, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Create a new follow-up entry",
        request_body=UserUserFollowUpInputSerializer,
        responses={201: UserUserFollowUpOutputSerializer()},
        tags=["Follow Ups"]
    )
    def create(self, request):
        serializer = UserUserFollowUpInputSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            output = UserUserFollowUpOutputSerializer(instance)
            return Response(output.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserConsentViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="List all user consent records",
        responses={200: UserConsentOutputSerializer(many=True)},
        tags=["User Consent"]
    )
    def list(self, request):
        queryset = UserConsent.objects.all()
        serializer = UserConsentOutputSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Load or initialize a consent session using invite UUID",
        responses={200: UserConsentOutputSerializer},
        tags=["User Consent"]
    )
    def retrieve(self, request, pk=None):
        consent, created = retrieve_or_initialize_user_consent(pk)
        history, just_created = get_or_initialize_consent_history(pk)

        response_data = UserConsentOutputSerializer(consent).data
        response_data["chat"] = [
            {
                "node_id": entry.get("node_id", ""),
                "echo_user_response": entry.get("echo_user_response"),
                **entry.get("next_consent_sequence", {})
            }
            for entry in history if "next_consent_sequence" in entry
        ]
        # response_data["chat"] = history
        # import pdb; pdb.set_trace()
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="Create a new user consent record",
        request_body=UserConsentInputSerializer,
        responses={201: UserConsentOutputSerializer},
        tags=["User Consent"]
    )
    def create(self, request):
        serializer = UserConsentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(UserConsentOutputSerializer(instance).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update a user consent record",
        request_body=UserConsentInputSerializer,
        responses={200: UserConsentOutputSerializer},
        tags=["User Consent"]
    )
    def update(self, request, pk=None):
        instance = get_object_or_404(UserConsent, pk=pk)
        serializer = UserConsentInputSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(UserConsentOutputSerializer(updated).data)

    @swagger_auto_schema(
        operation_description="Delete a user consent record",
        tags=["User Consent"]
    )
    def destroy(self, request, pk=None):
        instance = get_object_or_404(UserConsent, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserConsentUrlViewSet(viewsets.ViewSet):
    lookup_field = 'username'
    # permission_classes = {permissions.IsAuthenticated}
    
    @swagger_auto_schema(
        operation_description="Retrieve a consent URL",
        responses={200: UserConsentUrlOutputSerializer(many=True)},
        tags=["Consent URLs"]
    )
    def get(self, request):
        """Retrieve all Follow up instances
        """
        follow_ups = UserConsentUrl.objects.all()
        serializer = UserUserFollowUpOutputSerializer(follow_ups, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Retrieve the latest consent URL for a user by username",
        responses={200: UserConsentUrlOutputSerializer},
        tags=["Consent URLs"]
    )
    
    def invite_link_by_username(self, request, username=None):
        user = get_object_or_404(User, username=username)
        invite = user.consent_urls.order_by('-created_at').first()

        if not invite:
            return Response({"detail": "No invite link found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserConsentUrlOutputSerializer(invite)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        operation_description="Create a consent URL",
        responses={200: UserOutputSerializer(many=True)},
        tags=["Consent URLs"]
    )
    def create(self, request):
        """Create the consent object"""
        serializer = UserConsentUrlInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                consent = serializer.save()
                return Response(UserConsentUrlOutputSerializer(consent).data, status=status.HTTP_200_OK)
            except:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserConsentResponseViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve the next part of the consent chat based on a node_id and invite_id.",
        query_serializer=UserConsentResponseInputSerializer,
        responses={200: UserConsentResponseOutputSerializer},
        tags=["Consent Response"]
    )
    def retrieve(self, request, pk=None):
        invite_id = pk
        node_id = request.query_params.get("node_id")
        serializer = UserConsentResponseInputSerializer(
            data={
                "invite_id": pk,
                "node_id": request.query_params.get("node_id")
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # serializer = UserConsentResponseInputSerializer(data={**request.query_params, 'invite_id': pk}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invite_id = str(data["invite_id"])
            node_id = data["node_id"]
            conversation_graph = get_script_from_invite_id(invite_id)

            if node_id == "start":
                start_node_id = get_consent_start_id(conversation_graph)
                first_sequence = process_workflow(start_node_id, invite_id)
                history = get_user_consent_history(invite_id)
                history.append({
                    "next_consent_sequence": first_sequence,
                    "echo_user_response": "",
                    "node_id": "start"
                })
                set_user_consent_history(invite_id, history)
                return Response(UserConsentResponseOutputSerializer({
                    "chat": history,
                    "next_node_id": start_node_id,
                    "end_sequence": first_sequence.get("end_sequence", False),
                }).data)

            echo_user_response = get_response(conversation_graph, node_id)
            metadata = conversation_graph[node_id].get("metadata", {})
            workflow = metadata.get("workflow")
            next_node_id = ""

            if workflow == "test_user_understanding":
                next_node_id = process_test_question(conversation_graph, node_id, invite_id)
            elif workflow in ["start_consent", "decline_consent"]:
                next_node_id = process_user_consent(conversation_graph, node_id, invite_id)
            elif workflow == "follow_up":
                create_follow_up_with_user(
                    invite_id,
                    metadata.get("follow_up_reason", ""),
                    metadata.get("follow_up_info", "")
                )

            if not next_node_id:
                children = conversation_graph[node_id].get("child_ids", [])
                next_node_id = children[0] if children else "terminal_node"

            next_sequence = process_workflow(next_node_id, invite_id)
            history = get_user_consent_history(invite_id)
            history.append({
                "next_consent_sequence": next_sequence,
                "echo_user_response": echo_user_response,
                "node_id": node_id,
            })
            # import pdb; pdb.set_trace()
            set_user_consent_history(invite_id, history)
            chat = [
                {
                    "node_id": entry.get("node_id", ""),
                    "echo_user_response": entry.get("echo_user_response"),
                    **entry.get("next_consent_sequence", {})
                }
                for entry in history if "next_consent_sequence" in entry
            ]
            print("next_node_id: ", next_node_id)
            return Response(UserConsentResponseOutputSerializer({
                "chat": chat,
                "next_node_id": next_node_id,
                "end_sequence": next_sequence.get("end_sequence", False),
            }).data)

        except Exception as e:
            return Response(UserConsentResponseOutputSerializer({
                "chat": [],
                "status": "error",
                "error": str(e)
            }).data, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Submit a form response during the consent chat.",
        request_body=UserConsentResponseInputSerializer,
        responses={200: UserConsentResponseOutputSerializer},
        tags=["Consent Response"]
    )
    def create(self, request):
        serializer = UserConsentResponseInputSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invite_id = str(data["invite_id"])
            form_type = data["form_type"]
            responses = data["form_responses"]
            conversation_graph = get_script_from_invite_id(invite_id)

            if form_type == "family_enrollment":
                result = handle_family_enrollment_form(conversation_graph, invite_id, responses)
            elif form_type == "contact_other_adult":
                result = handle_other_adult_contact_form(invite_id, responses)
            elif form_type == "child_contact":
                result = handle_child_contact_form(invite_id, responses)
            elif form_type == "feedback":
                result = handle_user_feedback_form(invite_id, responses)
            else:
                raise ValueError(f"Unknown form_type: {form_type}")

            return Response(UserConsentResponseOutputSerializer({
                "chat": result["chat"],
                "next_node_id": result.get("next_node_id"),
                "end_sequence": result["chat"][-1]["next_consent_sequence"].get("end_sequence", False),
            }).data)

        except Exception as e:
            return Response(UserConsentResponseOutputSerializer({
                "chat": [],
                "status": "error",
                "error": str(e),
            }).data, status=status.HTTP_400_BAD_REQUEST)


# class UserConsentResponseView(APIView):
#     """
#     Handles user response during the consent workflow.
#     """
#     permission_classes = [AllowAny]

#     def get(self, request, invite_id):
#         import pdb; pdb.set_trace()
#         node_id = request.query_params.get('node_id')
#         import pdb; pdb.set_trace()
#         if not node_id:
#             return Response({'error': 'Missing node ID'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             conversation_graph = get_script_from_invite_id(invite_id)

#             if node_id == 'start':
#                 start_node_id = get_consent_start_id(conversation_graph)
#                 first_sequence = process_workflow(start_node_id, invite_id)

#                 history = get_user_consent_history(invite_id)
#                 history.append({
#                     "next_consent_sequence": first_sequence,
#                     "echo_user_response": ""
#                 })
#                 set_user_consent_history(invite_id, history)

#                 return Response({"chat": history})

#             # Handle regular flow
#             echo_user_response = get_response(conversation_graph, node_id)
#             metadata = conversation_graph[node_id].get('metadata', {})
#             next_node_id = ''

#             workflow = metadata.get('workflow')
#             print("workflow type: ", workflow, node_id)
#             if workflow == 'test_user_understanding':
#                 next_node_id = process_test_question(conversation_graph, node_id, invite_id)

#             elif workflow == 'start_consent':
#                 import pdb; pdb.set_trace()
#                 next_node_id = process_user_consent(conversation_graph, node_id, invite_id)
#             elif workflow == 'follow_up':
#                 create_follow_up_with_user(
#                     invite_id,
#                     metadata.get('follow_up_reason', ''),
#                     metadata.get('follow_up_info', '')
#                 )
#             elif workflow == 'decline_consent':
#                 next_node_id = process_user_consent(conversation_graph, node_id, invite_id)

#             if not next_node_id:
#                 children = conversation_graph[node_id].get('child_ids', [])
#                 next_node_id = children[0] if children else 'terminal_node'

#             next_sequence = process_workflow(next_node_id, invite_id)

#             # Update chat history

#             history = get_user_consent_history(invite_id)
#             history.append({
#                 "next_consent_sequence": next_sequence,
#                 "echo_user_response": echo_user_response,
#                 "node_id": node_id,
#             })
#             set_user_consent_history(invite_id, history)

#             return Response({"chat": history})

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
