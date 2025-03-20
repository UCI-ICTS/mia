from django.shortcuts import render

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import User, UserChatUrl, UserConsent, ConsentAgeGroup, UserFeedback, Chat
from .utils import (
    get_script_from_invite_id, get_chat_start_id, process_workflow, get_response,
    generate_workflow, process_test_question, process_user_consent, create_follow_up_with_user,
    clean_up_after_chat, get_user_workflow, set_user_workflow, set_user_chat_history, get_user_chat_history
)

@method_decorator(login_required, name='dispatch')
class UserInviteView(View):
    def get(self, request, invite_id):
        user_chat_history = get_user_chat_history(invite_id)
        if not user_chat_history:
            next_chat_sequence = {
                'user_responses': [('start', 'Start')],
                'user_html_type': 'button'
            }
            return render(request, 'splash_chat.html', {'next_chat_sequence': next_chat_sequence})

        workflow = get_user_workflow(invite_id)
        if workflow is None:
            set_user_workflow(invite_id, [])

        return render(request, 'chat.html', {'next_chat_sequence': user_chat_history})

@method_decorator(login_required, name='dispatch')
class UserResponseView(View):
    def get(self, request, invite_id):
        try:
            conversation_graph = get_script_from_invite_id(invite_id)
            user_response_node_id = request.GET.get('id')
            if user_response_node_id == 'start':
                start_node_id = get_chat_start_id(conversation_graph)
                next_chat_sequence = process_workflow(start_node_id, invite_id)
                user_chat_history = get_user_chat_history(invite_id)
                user_chat_history.append({'next_chat_sequence': next_chat_sequence, 'echo_user_response': ''})
                set_user_chat_history(invite_id, user_chat_history)
                return JsonResponse({'reload': True})
            else:
                echo_user_response = get_response(conversation_graph, user_response_node_id)
                node_metadata = conversation_graph[user_response_node_id]['metadata']
                next_node_id = ''

                if node_metadata['workflow'] == 'test_user_understanding':
                    next_node_id = process_test_question(conversation_graph, user_response_node_id, invite_id)
                elif node_metadata['workflow'] == 'start_consent':
                    next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)
                elif node_metadata['workflow'] == 'follow_up':
                    create_follow_up_with_user(invite_id, node_metadata['follow_up_reason'], node_metadata['follow_up_info'])
                elif node_metadata['workflow'] == 'decline_consent':
                    next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)

                if not next_node_id:
                    next_node_id = conversation_graph[user_response_node_id]['child_ids'][0] if conversation_graph[user_response_node_id]['child_ids'] else 'terminal_node'

                next_chat_sequence = process_workflow(next_node_id, invite_id)
                set_user_chat_history(invite_id, next_chat_sequence)
                return JsonResponse({'echo_user_response': echo_user_response, 'next_chat_sequence': next_chat_sequence})
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

@method_decorator(login_required, name='dispatch')
class CreateUserFeedbackView(View):
    def post(self, request, invite_id):
        user_id = get_object_or_404(UserChatUrl, chat_url=str(invite_id)).user_id
        satisfaction = request.POST.get('satisfaction', '')
        suggestions = request.POST.get('suggestions', '')[:2000]  # Limit text length
        
        user_feedback = UserFeedback.objects.create(
            user_id=user_id,
            satisfaction=satisfaction,
            suggestions=suggestions
        )
        user_feedback.save()
        
        return JsonResponse({'message': 'Feedback submitted successfully'})
