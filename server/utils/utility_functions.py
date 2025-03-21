import json
import os
from datetime import datetime, timedelta
from django.db import transaction
from django.core.cache import cache
from django.db.models import Count, Max
from chat.models import Chat, ChatScriptVersion
from authentication.models import User, UserChatUrl, UserTest, UserConsent, ConsentAgeGroup, UserFollowUp


def get_script_from_invite_id(invite_id):
    """Retrieve the chat script from an invite ID."""
    try:
        return (
            ChatScriptVersion.objects.filter(
                chat_id=User.objects.get(user_chat_urls__chat_url=str(invite_id)).chat_script_version_id
            )
            .values_list("script", flat=True)
            .first()
        )
    except User.DoesNotExist:
        raise ValueError(f"ERROR: script not found for {invite_id}")


def get_chat_start_id(conversation_graph):
    """Find the starting node in the conversation graph."""
    for node_id, node in conversation_graph.items():
        if node.get("parent_ids") and node["parent_ids"][0] == "start":
            return node_id
    raise ValueError("ERROR: conversation_graph start key not found")


def get_response(conversation_graph, node_id):
    """Retrieve bot or user response from the conversation graph."""
    node = conversation_graph.get(node_id, {})
    if node.get("html_type") == "form":
        return node.get("html_content")
    elif node.get("type") == "user":
        return node.get("messages", [])[0]
    return node.get("messages", [])


def process_workflow(chat_id, invite_id):
    """Process workflow logic based on user interactions."""
    conversation_graph = get_script_from_invite_id(invite_id)
    workflow = cache.get(f"user_workflow_{invite_id}", [])

    if workflow and chat_id in workflow[0]:
        next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)
        workflow[0] = [node for node in workflow[0] if node not in node_ids]
        if not workflow[0] or next_chat_sequence.get("end_sequence"):
            workflow.pop(0)
            cache.set(f"user_workflow_{invite_id}", workflow)
    else:
        next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)

    return next_chat_sequence


def get_next_chat_sequence(conversation_graph, node_id):
    """Determine the next chat sequence in the conversation."""
    bot_messages = []
    user_responses = []
    node_ids = []
    queue = [node_id]
    end_sequence = []

    while queue:
        current_node_id = queue.pop(0)
        node = conversation_graph.get(current_node_id)
        if "end_sequence" in node.get("metadata", {}):
            end_sequence.append(node["metadata"]["end_sequence"])

        if node["type"] == "bot":
            bot_messages.extend(get_response(conversation_graph, current_node_id))
            queue.extend(node.get("child_ids", []))
        else:
            user_responses.append((current_node_id, get_response(conversation_graph, current_node_id)))

        node_ids.append(current_node_id)

    return {
        "bot_messages": bot_messages,
        "user_responses": user_responses,
        "user_html_type": "form" if len(conversation_graph[node_id]["child_ids"]) == 1 and
                                    conversation_graph[conversation_graph[node_id]["child_ids"][0]].get("html_type") == "form"
                                    else "button",
        "end_sequence": any(end_sequence),
    }, node_ids


def save_test_question(conversation_graph, current_node_id, user, chat_script_version_id):
    """Save user responses to test questions."""
    node = conversation_graph.get(current_node_id)
    if node.get("metadata", {}).get("test_question_answer_correct") and node["type"] == "user":
        parent_id = node["parent_ids"][0]
        parent_node = conversation_graph.get(parent_id, {})
        if parent_node.get("metadata", {}).get("test_question"):
            UserTest.objects.create(
                user=user,
                chat_script_version_id=chat_script_version_id,
                test_try_num=user.num_test_tries,
                test_question=parent_node["messages"][0],
                user_answer=node["messages"][0],
                answer_correct=node["metadata"]["test_question_answer_correct"],
            )


def get_test_results(user, chat_script_version_id):
    """Retrieve the number of correct test responses for a user."""
    return (
        UserTest.objects.filter(
            user=user,
            chat_script_version_id=chat_script_version_id,
            test_try_num=user.num_test_tries,
            answer_correct=True,
        )
        .aggregate(correct_count=Count("answer_correct"))["correct_count"]
        or 0
    )


def create_follow_up_with_user(invite_id, reason, more_info):
    """Create a follow-up entry for a user."""
    user = User.objects.get(user_chat_urls__chat_url=str(invite_id))
    UserFollowUp.objects.create(user=user, follow_up_reason=reason, follow_up_info=more_info)


def clean_up_after_chat(invite_id):
    """Mark chat URL as expired 24 hours after conversation ends."""
    user_chat_url = UserChatUrl.objects.get(chat_url=str(invite_id))
    user_chat_url.expires_at = datetime.now() + timedelta(hours=24)
    user_chat_url.save()


def _replace_db_script_with_json(chat_name, json_file):
    """Replace an existing chat script with a JSON file."""
    try:
        chat = Chat.objects.get(name=chat_name)
        version = ChatScriptVersion.objects.filter(chat=chat).aggregate(Max("version_number"))["version_number__max"]
        chat_script_version = ChatScriptVersion.objects.get(chat=chat, version_number=version)

        if os.path.exists(json_file):
            with open(json_file, "r") as file:
                chat_script_version.script = json.load(file)

        chat_script_version.save()
        print("Saved!")
    except Chat.DoesNotExist:
        raise ValueError(f"Chat with name {chat_name} not found.")
