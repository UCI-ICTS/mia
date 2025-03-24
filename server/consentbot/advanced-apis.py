#!/usr/bin/env python
# consentbot/apis.py

# from datetime import datetime
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from django.shortcuts import get_object_or_404
# from authentication.models import User, UserConsentUrl, UserFeedback, ConsentAgeGroup
# from utils.cache import get_user_workflow, set_user_workflow, set_user_consent_history, get_user_consent_history
# from utils.utility_functions import (
#     get_script_from_invite_id,
#     get_consent_start_id,
#     process_workflow,
#     get_response,
#     generate_workflow,
#     process_test_question,
#     process_user_consent,
#     create_follow_up_with_user,
#     clean_up_after_consent,
# )
# from utils.enumerations import CONSENT_STATEMENTS
# from consentbot.models import Consent

# class UserInviteAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Initialize or resume a consent session",
#         responses={200: openapi.Response("Consent sequence", examples={
#             "application/json": {
#                 "next_consent_sequence": {}
#             }
#         })},
#         tags=["Consent"]
#     )
#     def get(self, request, invite_id):
#         user_consent_history = get_user_consent_history(invite_id)
#         if not user_consent_history:
#             next_consent_sequence = {
#                 'user_responses': [('start', 'Start')],
#                 'user_html_type': 'button'
#             }
#             return Response({'next_consent_sequence': next_consent_sequence}, status=status.HTTP_200_OK)

#         workflow = get_user_workflow(invite_id)
#         if workflow is None:
#             set_user_workflow(invite_id, [])

#         return Response({'next_consent_sequence': user_consent_history}, status=status.HTTP_200_OK)


# class UserResponseAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Handle user response and return the next consent sequence",
#         manual_parameters=[
#             openapi.Parameter('id', openapi.IN_QUERY, description="Node ID", type=openapi.TYPE_STRING)
#         ],
#         responses={200: openapi.Response("Next consent sequence")},
#         tags=["Consent"]
#     )
#     def get(self, request, invite_id):
#         try:
#             conversation_graph = get_script_from_invite_id(invite_id)
#             user_response_node_id = request.GET.get('id')

#             if user_response_node_id == 'start':
#                 start_node_id = get_consent_start_id(conversation_graph)
#                 next_consent_sequence = process_workflow(start_node_id, invite_id)
#                 user_consent_history = get_user_consent_history(invite_id)
#                 user_consent_history.append({'next_consent_sequence': next_consent_sequence, 'echo_user_response': ''})
#                 set_user_consent_history(invite_id, user_consent_history)
#                 return Response({'reload': True})

#             echo_user_response = get_response(conversation_graph, user_response_node_id)
#             node_metadata = conversation_graph[user_response_node_id].get('metadata', {})
#             next_node_id = ''

#             workflow_type = node_metadata.get('workflow')
#             if workflow_type == 'test_user_understanding':
#                 next_node_id = process_test_question(conversation_graph, user_response_node_id, invite_id)
#             elif workflow_type == 'start_consent':
#                 next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)
#             elif workflow_type == 'follow_up':
#                 create_follow_up_with_user(
#                     invite_id,
#                     node_metadata.get('follow_up_reason', ''),
#                     node_metadata.get('follow_up_info', '')
#                 )
#             elif workflow_type == 'decline_consent':
#                 next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)

#             if not next_node_id:
#                 children = conversation_graph[user_response_node_id].get('child_ids', [])
#                 next_node_id = children[0] if children else 'terminal_node'

#             next_consent_sequence = process_workflow(next_node_id, invite_id)
#             set_user_consent_history(invite_id, next_consent_sequence)

#             return Response({
#                 'echo_user_response': echo_user_response,
#                 'next_consent_sequence': next_consent_sequence
#             })
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class CreateUserFeedbackAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Submit user feedback",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['satisfaction', 'suggestions'],
#             properties={
#                 'satisfaction': openapi.Schema(type=openapi.TYPE_STRING),
#                 'suggestions': openapi.Schema(type=openapi.TYPE_STRING),
#             }
#         ),
#         responses={201: openapi.Response("Feedback created")},
#         tags=["Feedback"]
#     )
#     def post(self, request, invite_id):
#         user_consent_url = get_object_or_404(UserConsentUrl, consent_url=str(invite_id))
#         user_id = user_consent_url.user_id

#         satisfaction = request.data.get('satisfaction', '')
#         suggestions = request.data.get('suggestions', '')[:2000]  # Limit text length

#         UserFeedback.objects.create(
#             user_id=user_id,
#             satisfaction=satisfaction,
#             suggestions=suggestions
#         )

#         return Response({'message': 'Feedback submitted successfully'}, status=status.HTTP_201_CREATED)


# class ContactAnotherAdultAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(auto_schema=None)
#     def post(self, request, invite_id):
#         submitted = request.data.get('submit') == 'true'
#         node_id = request.data.get('id_submit_node') or request.data.get('id_skip_node')

#         echo_user_response = "Let's skip this"

#         if submitted:
#             user_consent_url = get_object_or_404(UserConsentUrl, consent_url=str(invite_id))
#             user = get_object_or_404(User, pk=user_consent_url.user_id)
#             user_consent = get_object_or_404(Consent, pk=user.consent_script_version.consent_id)

#             new_user = User.objects.create(
#                 first_name=request.data.get('firstname', ''),
#                 last_name=request.data.get('lastname', ''),
#                 email=request.data.get('email', ''),
#                 phone=request.data.get('phone', ''),
#                 consent_name=user_consent.name,
#                 referred_by=user.user_id
#             )
#             echo_user_response = 'Submitted!'

#         next_consent_sequence = process_workflow(node_id, invite_id)
#         update_user_consent_history(echo_user_response, next_consent_sequence, invite_id)
#         return Response({"echo_user_response": echo_user_response, "next_consent_sequence": next_consent_sequence})


# class FamilyEnrollmentAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(auto_schema=None)
#     def post(self, request, invite_id):
#         conversation_graph = get_script_from_invite_id(invite_id)
#         parent_id = request.data.get('id_node')
#         parent_node = conversation_graph.get(parent_id)
#         user_id = get_object_or_404(UserConsentUrl, consent_url=str(invite_id)).user_id
#         user = get_object_or_404(User, pk=user_id)

#         checkbox_workflow_ids = []
#         checked_checkboxes = []

#         if request.data.get('myself'):
#             checked_checkboxes.append('Myself')
#             checkbox_workflow_ids.append(request.data.get('id_myself'))
#             user.enrolling_myself = True

#         if request.data.get('childOtherParent'):
#             checked_checkboxes.append("My child's other parent")
#             checkbox_workflow_ids.append(request.data.get('id_childOtherParent'))

#         if request.data.get('adultFamilyMember'):
#             checked_checkboxes.append("Another adult family member")
#             checkbox_workflow_ids.append(request.data.get('id_adultFamilyMember'))

#         if request.data.get('myChildChildren'):
#             checked_checkboxes.append('My child/children')
#             checkbox_workflow_ids.append(request.data.get('id_myChildChildren'))
#             user.enrolling_children = True

#         user.save()
#         checkbox_workflow_ids = list(dict.fromkeys(checkbox_workflow_ids))
#         start_node_id = checkbox_workflow_ids[0]

#         generate_workflow(start_node_id, checkbox_workflow_ids, invite_id)
#         next_consent_sequence = process_workflow(start_node_id, invite_id)
#         echo_user_response = ', '.join(checked_checkboxes)
#         update_user_consent_history(echo_user_response, next_consent_sequence, invite_id)

#         return Response({"echo_user_response": echo_user_response, "next_consent_sequence": next_consent_sequence})


# class ChildrenEnrollmentAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(auto_schema=None)
#     def post(self, request, invite_id):
#         conversation_graph = get_script_from_invite_id(invite_id)
#         parent_id = request.data.get('id_node')
#         user_id = get_object_or_404(UserConsentUrl, consent_url=str(invite_id)).user_id
#         user = get_object_or_404(User, pk=user_id)

#         num_children = int(request.data.get('numChildrenEnroll'))
#         user.num_children_enrolling = num_children
#         user.save()

#         if num_children <= 3:
#             echo_user_response = f"Enrolling {num_children} {'child' if num_children == 1 else 'children'}"
#             child_node_id = request.data.get('one-three')
#             for _ in range(num_children):
#                 generate_workflow(child_node_id, [child_node_id], invite_id)
#         else:
#             echo_user_response = 'Enrolling 4 or more children'
#             child_node_id = request.data.get('four-more')
#             create_follow_up_with_user(invite_id, 'consent', 'enroll 4 or more children')

#         next_consent_sequence = process_workflow(child_node_id, invite_id)
#         update_user_consent_history(echo_user_response, next_consent_sequence, invite_id)

#         return Response({"echo_user_response": echo_user_response, "next_consent_sequence": next_consent_sequence})


# class SaveConsentPreferencesAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(auto_schema=None)
#     def post(self, request, invite_id):
#         conversation_graph = get_script_from_invite_id(invite_id)
#         parent_id = request.data.get('id_node')
#         user_consent = None

#         if get_consenting_myself(invite_id):
#             user_id = get_object_or_404(UserConsentUrl, consent_url=str(invite_id)).user_id
#             user = get_object_or_404(User, pk=user_id)
#             user_consent = get_object_or_404(UserConsent, user_id=user_id)
#         elif get_consenting_children(invite_id):
#             user = get_object_or_404(User, pk=get_child_user_id(invite_id))
#             user_consent = get_object_or_404(UserConsent, pk=get_child_user_consent_id(invite_id))

#         echo_user_response = "Submitted preferences"

#         def update_bool(field, key):
#             val = request.data.get(key)
#             if val:
#                 setattr(user_consent, field, val == 'yes')

#         update_bool('store_sample_this_study', 'storeSamplesThisStudy')
#         update_bool('store_sample_other_studies', 'storeSamplesOtherStudies')
#         update_bool('store_phi_this_study', 'storePhiThisStudy')
#         update_bool('store_phi_other_studies', 'storePhiOtherStudies')
#         update_bool('return_primary_results', 'rorPrimary')
#         update_bool('return_actionable_secondary_results', 'rorSecondary')
#         update_bool('return_secondary_results', 'rorSecondaryNot')

#         if request.data.get('fullname'):
#             user_consent.user_full_name_consent = request.data.get('fullname')

#         if request.data.get('consent'):
#             user_consent.consented_at = datetime.now()
#             user_consent.consent_statements = CONSENT_STATEMENTS
#             if request.data.get('childname'):
#                 user_consent.child_full_name_consent = request.data.get('childname')
#             user.consent_complete = True
#             user.save()
#             echo_user_response = 'I consent to this study'

#         user_consent.save()
#         next_node_id = process_user_consent(conversation_graph, parent_id, invite_id)
#         if not next_node_id:
#             next_node_id = conversation_graph[parent_id]['child_ids'][0]

#         next_consent_sequence = process_workflow(next_node_id, invite_id)
#         update_user_consent_history(echo_user_response, next_consent_sequence, invite_id)

#         return Response({"echo_user_response": echo_user_response, "next_consent_sequence": next_consent_sequence})
