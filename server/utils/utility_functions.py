#!/usr/bin/env python
# utils/utility_functions.py

import json
import os
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Max
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from consentbot.models import ConsentScript
from authentication.models import User, UserConsentUrl, UserTest, UserConsent, ConsentAgeGroup, UserFollowUp

# flags
NUM_TEST_QUESTIONS_CORRECT = 10
NUM_TEST_TRIES = 2

def get_script_from_invite_id(invite_id):
    """Retrieve the consent script JSON from a UserConsentUrl UUID."""
    try:
        consent_id = UserConsentUrl.objects.get(consent_url=invite_id).user.consent_script_id
        if not consent_id:
            raise ValueError("User does not have a consent_script assigned.")
        return ConsentScript.objects.get(consent_id=consent_id).script
    except UserConsentUrl.DoesNotExist:
        raise ValueError(f"Invite ID {invite_id} not found.")
    except ConsentScript.DoesNotExist:
        raise ValueError(f"ConsentScript for invite ID {invite_id} not found.")


def get_consent_start_id(conversation_graph):
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


def process_workflow(consent_id, invite_id):
    """Process workflow logic based on user interactions."""
    conversation_graph = get_script_from_invite_id(invite_id)
    workflow = cache.get(f"user_workflow_{invite_id}", [])

    if workflow and consent_id in workflow[0]:
        next_consent_sequence, node_ids = get_next_consent_sequence(conversation_graph, consent_id)
        workflow[0] = [node for node in workflow[0] if node not in node_ids]
        if not workflow[0] or next_consent_sequence.get("end_sequence"):
            workflow.pop(0)
            cache.set(f"user_workflow_{invite_id}", workflow)
    else:
        next_consent_sequence, node_ids = get_next_consent_sequence(conversation_graph, consent_id)

    return next_consent_sequence


def get_next_consent_sequence(conversation_graph, node_id):
    """Determine the next consent sequence in the conversation."""
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


def save_test_question(conversation_graph, current_node_id, user, consent_script_version_id):
    """Save user responses to test questions."""
    node = conversation_graph.get(current_node_id)
    if node.get("metadata", {}).get("test_question_answer_correct") and node["type"] == "user":
        parent_id = node["parent_ids"][0]
        parent_node = conversation_graph.get(parent_id, {})
        if parent_node.get("metadata", {}).get("test_question"):
            UserTest.objects.create(
                user=user,
                consent_script_version_id=consent_script_version_id,
                test_try_num=user.num_test_tries,
                test_question=parent_node["messages"][0],
                user_answer=node["messages"][0],
                answer_correct=node["metadata"]["test_question_answer_correct"],
            )


def get_test_results(user, consent_script_version_id):
    """Retrieve the number of correct test responses for a user."""
    return (
        UserTest.objects.filter(
            user=user,
            consent_script_version_id=consent_script_version_id,
            test_try_num=user.num_test_tries,
            answer_correct=True,
        )
        .aggregate(correct_count=Count("answer_correct"))["correct_count"]
        or 0
    )


def create_follow_up_with_user(invite_id, reason, more_info):
    """Create a follow-up entry for a user."""

    consent_url = UserConsentUrl.objects.get(consent_url=invite_id)
    user = consent_url.user
    UserFollowUp.objects.create(user=user, follow_up_reason=reason, follow_up_info=more_info)


def clean_up_after_consent(invite_id):
    """Mark consent URL as expired 24 hours after conversation ends."""
    user_consent_url = UserConsentUrl.objects.get(consent_url=str(invite_id))
    user_consent_url.expires_at = timezone.now() + timedelta(hours=24)
    user_consent_url.save()


# def _replace_db_script_with_json(consent_name, json_file):
#     """Replace an existing consent script with a JSON file."""
#     try:
#         consent = ConsentScript.objects.get(name=consent_name)
#         version = ConsentScript.objects.filter(chat=chat).aggregate(Max("version_number"))["version_number__max"]
#         chat_script_version = ConsentScript.objects.get(chat=chat, version_number=version)

#         if os.path.exists(json_file):
#             with open(json_file, "r") as file:
#                 chat_script_version.script = json.load(file)

#         chat_script_version.save()
#         print("Saved!")
#     except Chat.DoesNotExist:
#         raise ValueError(f"Chat with name {chat_name} not found.")




def generate_workflow(start_node_id, user_option_node_ids, invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)

    # generate a sub workflow to dynamically process user responses
    workflow = get_user_workflow(invite_id)

    metadata_field = conversation_graph[start_node_id]['metadata']['workflow']
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(conversation_graph, user_option_node_id, metadata_field)
        workflow.append(sub_graph)
    set_user_workflow(invite_id, workflow)
    return workflow


from django.shortcuts import get_object_or_404

def process_test_question(conversation_graph, current_node_id, invite_id):
    node_metadata = conversation_graph.get(current_node_id, {}).get("metadata", {})
    
    if node_metadata.get("workflow") != "test_user_understanding":
        return ''

    try:
        # Get user from invite
        consent_url = get_object_or_404(UserConsentUrl, consent_url=str(invite_id))
        user = consent_url.user
        script_version = getattr(user, "consent_script_version", None)

        if not script_version:
            return node_metadata.get("fail_node_id", "")

        # Save current test question for tracking
        save_test_question(conversation_graph, current_node_id, user, script_version.pk)

        # If this is the end of the test sequence
        if node_metadata.get("end_sequence") is True:
            correct = get_test_results(user, script_version.pk)

            if correct < NUM_TEST_QUESTIONS_CORRECT:
                if user.num_test_tries < NUM_TEST_TRIES:
                    user.num_test_tries += 1
                    user.save(update_fields=["num_test_tries"])
                    return node_metadata.get("retry_node_id", "")
                else:
                    return node_metadata.get("fail_node_id", "")
            else:
                return node_metadata.get("pass_node_id", "")

    except UserConsentUrl.DoesNotExist:
        # If the invite ID is invalid
        return node_metadata.get("fail_node_id", "")
    
    except Exception as e:
        # Log it for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing test question: {e}")
        return node_metadata.get("fail_node_id", "")

    return ''


def process_user_consent(conversation_graph, current_node_id, invite_id):
    node = conversation_graph[current_node_id]['metadata']
    if node['workflow'] in ['start_consent', 'end_consent']:
        user_id = UserConsentUrl.query.filter_by(consent_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)

        # first we check if you're enrolling yourself and do that first
        if user.enrolling_myself and user.consent_complete is False:
            # create user consent db entry
            adult = ConsentAgeGroup.EIGHTEEN_AND_OVER
            user_consent = UserConsent(
                user_id=user.user_id,
                consent_age_group=adult
            )
            db.session.add(user_consent)
            db.session.commit()
            set_consenting_myself(invite_id, True)
            set_consent_node(invite_id, current_node_id)
            return node['enrolling_myself_node_id']

        # then we'll check if you're enrolling children
        elif user.enrolling_children:
            set_consenting_myself(invite_id, False)
            if get_consenting_children(invite_id) is None:
                set_consenting_children(invite_id, True)
                consent_node_id = get_consent_node(invite_id)
                node = conversation_graph[consent_node_id]['metadata']
                return node['enrolling_children_node_id']

    elif node['workflow'] == 'decline_consent':
        user_id = UserConsentUrl.query.filter_by(consent_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)

        user.declined_consent = True
        db.session.commit()

    return ''