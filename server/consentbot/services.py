#!/usr/bin/env python
# consentbot/serializers.py

import datetime
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import Optional
from authentication.services import FeedbackInputSerializer
from consentbot.models import (
    Consent,
    ConsentAgeGroup,
    ConsentScript,
    ConsentTestAnswer,
    ConsentTestAttempt,
    ConsentUrl,
)
from consentbot.selectors import (
    build_chat_from_history,
    format_turn,
    get_script_from_invite_id,
    get_next_consent_sequence,
    get_consent_start_id,
    get_user_label
)

from utils.cache import (
    get_user_consent_history,
    set_user_consent_history,
    get_user_workflow,
    set_user_workflow,
    set_consenting_myself,
    set_consent_node,
    get_consenting_children,
    set_consenting_children,
    get_consent_node
) 

User = get_user_model()  
# flags
PERCENT_TEST_QUESTIONS_CORRECT = 100
NUM_TEST_TRIES = 2


class RenderBlockSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["button", "form"])
    fields = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Used only if render.type == 'form'"
    )


class ConsentInputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    dependent_user_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Consent
        fields = [
            'user_id',
            'dependent_user_id',
            'consent_age_group',
            'consent_script',
            'store_sample_this_study',
            'store_sample_other_studies',
            'store_phi_this_study',
            'store_phi_other_studies',
            'return_primary_results',
            'return_actionable_secondary_results',
            'return_secondary_results',
            'consent_statements',
            'user_full_name_consent',
            'child_full_name_consent',
            'consented_at'
        ]

    def create(self, validated_data):
        user = User.objects.get(user_id=validated_data.pop('user_id'))
        dependent_user = None

        if 'dependent_user_id' in validated_data:
            dependent_user_id = validated_data.pop('dependent_user_id')
            if dependent_user_id:
                dependent_user = User.objects.get(user_id=dependent_user_id)

        # 🔍 Find latest consent URL for the user
        invite = ConsentUrl.objects.filter(user=user).order_by('-created_at').first()
        if not invite:
            raise serializers.ValidationError("No invite URL found for this user.")

        # 🔍 Lookup the ConsentScript based on the invite
        consent_script = get_script_from_invite_id(invite.consent_url)

        return Consent.objects.create(
            user=user,
            dependent_user=dependent_user,
            consent_script=consent_script,
            **validated_data
        )


class ConsentOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    dependent_user_id = serializers.UUIDField(source='dependent_user.user_id', read_only=True)
    dependent_email = serializers.EmailField(source='dependent_user.email', read_only=True)

    class Meta:
        model = Consent
        fields = [
            'user_consent_id',
            'user_id',
            'email',
            'dependent_user_id',
            'dependent_email',
            'consent_age_group',
            'store_sample_this_study',
            'store_sample_other_studies',
            'store_phi_this_study',
            'store_phi_other_studies',
            'return_primary_results',
            'return_actionable_secondary_results',
            'return_secondary_results',
            'consent_statements',
            'user_full_name_consent',
            'child_full_name_consent',
            'consented_at',
            'created_at'
        ]


class ConsentScriptInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentScript
        fields = [
            "name",
            "description",
            "derived_from",
            "version_number",
            "script"
        ]
        extra_kwargs = {
            "derived_from": {"required": False, "allow_null": True},
        }


class ConsentScriptOutputSerializer(serializers.ModelSerializer):
    derived_from = serializers.StringRelatedField()
    versions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    script = serializers.DictField(
        child=serializers.DictField(
            help_text="Each node in the conversation graph",
            child=serializers.JSONField()
        ),
        help_text="Consent conversation graph keyed by node_id. Each value is a node dict with type, messages, child_ids, parent_ids, render, metadata, etc."
    )

    class Meta:
        model = ConsentScript
        fields = [
            "script_id",
            "name",
            "description",
            "created_at",
            "derived_from",
            "version_number",
            "script",
            "versions"
        ]


class ConsentResponseInputSerializer(serializers.Serializer):
    invite_id = serializers.UUIDField(
        help_text="UUID of the invite link provided to the user."
    )
    node_id = serializers.CharField(
        required=False,
        help_text="ID of the current node in the conversation graph. Required for GET requests."
    )
    form_type = serializers.CharField(
        required=False,
        help_text="Type of form being submitted. Required for POST requests."
    )
    form_responses = serializers.ListField(
        child=serializers.DictField(
            child=serializers.JSONField(allow_null=True)
        ),
        required=False,
        help_text="List of form response objects. Supports string, boolean, or null values."
    )


    def validate(self, data):
        method = self.context['request'].method
        if method == 'POST':
            if not data.get('form_type'):
                raise serializers.ValidationError("'form_type' is required for POST requests.")
            if 'form_responses' not in data:
                raise serializers.ValidationError("'form_responses' is required for POST requests.")
        elif method == 'GET':
            if not data.get('node_id'):
                raise serializers.ValidationError("'node_id' is required for GET requests.")
        return data


class ConsentUrlInputSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)

    class Meta:
        model = ConsentUrl
        fields = ['username']

    def create(self, validated_data):

        username = validated_data.pop('username')
        user = User.objects.get(username=username)

        return ConsentUrl.objects.create(user=user, **validated_data)


class ConsentUrlOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    invite_link = serializers.SerializerMethodField()

    class Meta:
        model = ConsentUrl
        fields = [
            'consent_url_id',
            'consent_url',
            'invite_link',
            'created_at',
            'expires_at',
            'user_id',
            'email',
        ]

    def get_invite_link(self, obj):
        base_url = getattr(settings, 'PUBLIC_HOSTNAME', 'https://genomics.icts.uci.edu')
        return f"{base_url}/consent/{obj.consent_url}/"


def clean_up_after_chat(invite_id):
    """Set the invite URL to expire 24 hours from now."""
    try:
        consent_url = ConsentUrl.objects.get(consent_url=str(invite_id))
        consent_url.expires_at = timezone.now() + datetime.timedelta(hours=24)
        consent_url.save()
    except ConsentUrl.DoesNotExist:
        # Log or raise if needed
        pass


def get_or_initialize_consent_history(invite_id):
    """
    Retrieve existing consent history for a given invite_id,
    or initialize it with the starting node and first chat sequence.

    Returns:
        tuple: (history, just_created)
    """
    history = get_user_consent_history(invite_id)
    if history:
        return history, False

    graph = get_script_from_invite_id(invite_id)
    start_node = get_consent_start_id(graph)
    sequence = process_consent_sequence(start_node, invite_id, graph=graph)

    history = [format_turn(graph, start_node, echo_user_response="", next_sequence=sequence)]
    set_user_consent_history(invite_id, history)
    return history, True


def get_or_initialize_user_consent(invite_id:str) -> bool:
    """
    Given an invite ID (UUID), retrieve the existing Consent or initialize one.

    Returns:
        tuple: (Consent instance, bool indicating if it was created)
    """
    # Get the ConsentUrl instance (or 404 if invalid/expired)
    invite = get_object_or_404(ConsentUrl, consent_url=invite_id)

    # Check for an existing Consent record
    existing = Consent.objects.filter(user=invite.user, dependent_user=None).order_by('-created_at').first()

    if existing:
        return existing, False

    # Otherwise, create a new Consent (with placeholder values)
    new_consent = Consent.objects.create(
        user=invite.user,
        consent_script = invite.user.consent_script,
        consent_age_group=ConsentAgeGroup.EIGHTEEN_AND_OVER  # Default; you can change this logic
    )

    return new_consent, True


def process_consent_sequence(
    node_id: str,
    invite_id: str,
    graph: Optional[dict] = None
) -> dict:
    """
    Process the next step in the consent chat graph from a given node.

    This retrieves the next bot message sequence and updates the cached
    workflow state by removing nodes that have already been visited.

    Args:
        node_id (str): The node to begin traversal from.
        invite_id (str): The session ID (usually a UUID) identifying the consent URL.
        graph (dict, optional): Parsed conversation graph. If None, it will be loaded from the invite ID.

    Returns:
        dict: A chat sequence dict containing:
            - messages: Bot messages
            - responses: User options (buttons or form)
            - render: Render metadata (form config)
            - end: Whether this sequence ends the conversation
            - visited: List of node IDs traversed in this step
    """
    sequence = None
    if graph is None:
        graph = get_script_from_invite_id(invite_id)
    node = graph.get(node_id, {})

    # Handle second test attempt traversal
    if (
        node.get("type") == "bot"
        and node.get("metadata", {}).get("workflow") == "test_user_understanding"
        # and node.get("metadata", {}).get("test_question") is True
    ):
        user = ConsentUrl.objects.get(consent_url=invite_id).user
        attempts = ConsentTestAttempt.objects.filter(
            user=user, consent_script_version=user.consent_script
        ).order_by("started_at")

        if len(attempts) == 2:
            if len(attempts[1].incorrect_question_ids()) > 0:
                node_id = "iH6N9fF"
            else:
                correct = set(attempts[0].correct_question_ids())
                sequence = get_next_consent_sequence(
                    graph,
                    node_id,
                    skip_correct_test_nodes=True,
                    correct_questions=correct
                )
    
    # Fallback to default behavior
    if sequence is None:
        sequence = get_next_consent_sequence(graph, node_id)
    
    # Update workflow cache
    workflow = get_user_workflow(invite_id)
    if workflow and workflow[0] and node_id in workflow[0]:
        workflow[0] = [n for n in workflow[0] if n not in sequence["visited"]]
        if not workflow[0] or sequence["end"]:
            workflow.pop(0)
        set_user_workflow(invite_id, workflow)

    return sequence


def append_chat_history(invite_id:str, chat_turn:dict):
    """
    Appends a chat turn to the user's consent chat history in cache.

    Args:
        invite_id (str): The invite UUID identifying the session.
        chat_turn (dict): A formatted chat turn dictionary using `format_turn`.
    """
    history = get_user_consent_history(invite_id)
    history.append(chat_turn)
    set_user_consent_history(invite_id, history)


def update_consent_and_advance(invite_id, node_id, graph, echo_user_response):
    if node_id not in graph:
        return [{"messages": [f"Invalid node: {node_id}"], "responses": []}]
    next_node_id = graph[node_id]["child_ids"][0]
    next_sequence = process_consent_sequence(next_node_id, invite_id)
    history = get_user_consent_history(invite_id)

    history.append(format_turn(graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)
    clean_up_after_chat(invite_id)

    return build_chat_from_history(invite_id)


def handle_sample_storage(graph, invite_id, responses):
    """
    Processes the 'sample storage' form by updating the user's consent record,
    saving chat state, and progressing the conversation.

    Args:
        conversation_graph (dict): The full consent script graph.
        invite_id (str): The invite UUID identifying the session.
        responses (list): List of form response dicts.

    Returns:
        list[dict]: Updated chat history for the frontend.
    """

    samples, node_id = responses[0]['value'], responses[1]['value']
    consent = Consent.objects.filter(user=ConsentUrl.objects.get(consent_url=invite_id).user).latest('created_at')
    consent.store_sample_this_study = True
    consent.store_sample_other_studies = (samples == "storeSamplesOtherStudies")
    consent.save()
    return update_consent_and_advance(invite_id, node_id, graph, "Sample use submitted!")


def handle_phi_use(graph, invite_id, responses):
    """
    Handles the form submission for PHI (Protected Health Information) usage consent.

    Updates the user's `Consent` object to reflect their PHI usage choices and 
    appends the next sequence of the chat to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    samples, node_id = responses[0]['value'], responses[1]['value']
    consent = Consent.objects.filter(user=ConsentUrl.objects.get(consent_url=invite_id).user).latest('created_at')
    consent.store_phi_this_study = True
    consent.store_phi_other_studies = (samples == "storePhiOtherStudies")
    consent.save()
    return update_consent_and_advance(invite_id, node_id, graph, "PHI use submitted!")


def handle_result_return(graph, invite_id, responses):
    """
    Handles the form submission for return of genetic results preferences.

    Updates the user's `Consent` object with their selected options and appends
    the next chat turn to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    response_dict = {r["name"]: r["value"] for r in responses}
    node_id = response_dict["node_id"]
    consent = Consent.objects.filter(user=ConsentUrl.objects.get(consent_url=invite_id).user).latest('created_at')
    consent.return_primary_results = response_dict.get("rorPrimary") is True
    consent.return_actionable_secondary_results = response_dict.get("rorSecondary") is True
    consent.return_secondary_results = response_dict.get("rorSecondaryNot") is True
    consent.save()
    return update_consent_and_advance(invite_id, node_id, graph, "Result return preferences submitted!")


def handle_consent(graph, invite_id, responses):
    """
    Handles the final user consent form submission.

    Stores the user's name, timestamps the consent, and marks the consent
    as complete. Also updates chat history with the next sequence.

    Args:
        conversation_graph (dict): The parsed consent script.
        invite_id (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    response_dict = {r["name"]: r["value"] for r in responses}
    node_id = response_dict["node_id"]
    user = ConsentUrl.objects.get(consent_url=invite_id).user
    consent = Consent.objects.filter(user=user).latest('created_at')

    if response_dict.get("consent"):
        consent.user_full_name_consent = response_dict.get("fullname", "")
        consent.consented_at = timezone.now()
        user.consent_complete = True
        user.save()
        consent.save()

    return update_consent_and_advance(invite_id, node_id, graph, "Consent submitted!")


def handle_family_enrollment_form(conversation_graph, invite_id, responses):
    """
    Processes the form where a user selects who they are enrolling (self, children, or both).
    Updates user flags, generates dynamic workflow, and advances the chat sequence.
    """
    checked = responses[0]["value"]
    user = ConsentUrl.objects.get(consent_url=invite_id).user
    history = get_user_consent_history(invite_id)
    parent_node_id = history[-1]["node_id"] if history else None

    if not parent_node_id or parent_node_id not in conversation_graph:
        raise Exception("Invalid or missing parent node")

    try:
        fields = history[-1]['responses'][0]['label']['fields']
        checkbox_node_ids = {f['name']: f['id_value'] for f in fields}
    except Exception:
        raise Exception("Checkbox fields missing from chat history")

    workflow_ids = []
    for item in checked:
        node_id = checkbox_node_ids.get(item)
        if node_id:
            workflow_ids.append(node_id)
            if item == "myself":
                user.enrolling_myself = True
            elif item == "myChildChildren":
                user.enrolling_children = True
        else:
            print(f"[warning] {item} not in checkbox_node_ids")

    user.save()

    # Create sub-workflow and get next sequence
    start_node_id = workflow_ids[0]
    generate_workflow(start_node_id, workflow_ids, invite_id)
    next_sequence = process_consent_sequence(start_node_id, invite_id)

    history.append(format_turn(conversation_graph, start_node_id, ", ".join(checked), next_sequence))
    set_user_consent_history(invite_id, history)

    return build_chat_from_history(invite_id)


def handle_user_feedback_form(graph, invite_id, responses):
    """
    Handles submission of a feedback form, stores the data,
    and advances the chat sequence.

    Args:
        invite_id (str): The invite UUID identifying the session.
        responses (list): List of form response dicts.

    Returns:
        list[dict]: Updated chat history for the frontend.
    """

    data = {r["name"]: r["value"] for r in responses}
    node_id = data["node_id"]

    payload = {
        "satisfaction": data.get("satisfaction", ""),
        "suggestions": (data.get("suggestions") or "")[:2000]
    }

    user = ConsentUrl.objects.get(consent_url=invite_id).user
    if data.get("anonymize") is None:
        payload["user"] = user.pk

    serializer = FeedbackInputSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return update_consent_and_advance(invite_id, node_id, graph, "Feedback submitted!")


def handle_other_adult_contact_form(conversation_graph, invite_id, responses):
    """
    Processes the form submission where the user wants to refer another adult.
    This creates a new user record and progresses the chat.

    Args:
        conversation_graph (dict): Parsed consent script graph.
        invite_id (str): The invite UUID.
        responses (list): Submitted form responses.

    Returns:
        list[dict]: Updated chat history for frontend.
    """
    response_dict = {r.get("name"): r.get("value") for r in responses if r.get("name")}
    node_id = response_dict.get("node_id")

    consent_url = get_object_or_404(ConsentUrl, consent_url=invite_id)
    referring_user = consent_url.user

    first_name = response_dict.get("firstname", "")
    last_name = response_dict.get("lastname", "")
    phone = response_dict.get("phone", "")
    email = response_dict.get("email", "")

    if email:  # Only create a referred user if an email was submitted
        new_user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            referred_by=referring_user,
            consent_script=referring_user.consent_script  # Inherit the current user's script
        )
        echo_user_response = "Submitted!"
    else:
        echo_user_response = "Let's skip this"

    next_node_id = conversation_graph[node_id]["child_ids"][0]
    next_sequence = process_consent_sequence(next_node_id, invite_id)

    history = get_user_consent_history(invite_id)
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(invite_id, history)

    return build_chat_from_history(invite_id)


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


def traverse(conversation_graph, start_id, metadata_field=None):
    sub_graph_nodes = set()
    visited = set()

    def dfs(node_id):
        if node_id in visited:
            return
        visited.add(node_id)

        node = conversation_graph.get(node_id, {})
        metadata = node.get('metadata', {})
        workflow = metadata.get('workflow')

        if metadata_field:
            if workflow != metadata_field:
                # Keep walking children even if this node doesn't match
                pass
            else:
                sub_graph_nodes.add(node_id)
        else:
            sub_graph_nodes.add(node_id)

        for child_id in node.get('child_ids', []):
            dfs(child_id)

    dfs(start_id)
    return list(sub_graph_nodes)


def process_test_question(conversation_graph, current_node_id, invite_id):
    node_metadata = conversation_graph.get(current_node_id, {}).get("metadata", {})
    
    if node_metadata.get("workflow") != "test_user_understanding":
        return ''

    try:
        # Get user and script
        consent_url = get_object_or_404(ConsentUrl, consent_url=str(invite_id))
        user = consent_url.user
        script_version = getattr(user, "consent_script", None)
        if not script_version:
            return node_metadata.get("fail_node_id", "")

        # Start or retrieve the current test attempt
        attempt, _ = ConsentTestAttempt.objects.get_or_create(
            user=user,
            consent_script_version=script_version,
            test_try_num=user.num_test_tries
        )

        # Save this question/response to the attempt
        save_test_question(conversation_graph, current_node_id, attempt)

        # Final question? Evaluate
        if node_metadata.get("end_sequence") is True or node_metadata.get("end_sequence") == 'true':
            test_pass = attempt.percent_correct() 
            if test_pass < PERCENT_TEST_QUESTIONS_CORRECT:
                if user.num_test_tries < NUM_TEST_TRIES:
                    user.num_test_tries += 1
                    user.save(update_fields=["num_test_tries"])
                    return node_metadata.get("retry_node_id", "")
                else:
                    return node_metadata.get("fail_node_id", "")
            else:
                return node_metadata.get("pass_node_id", "")

    except ConsentUrl.DoesNotExist:
        return node_metadata.get("fail_node_id", "")
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing test question: {e}")
        return node_metadata.get("fail_node_id", "")

    return ''

def save_test_question(conversation_graph, current_node_id, attempt):
    node = conversation_graph.get(current_node_id)
    if node.get("type") != "user":
        return

    parent_id = node.get("parent_ids", [None])[0]
    parent_node = conversation_graph.get(parent_id, {})

    if not parent_node.get("metadata", {}).get("test_question"):
        return

    question_text = parent_node.get("messages", [""])[0]
    user_answer = node.get("messages", [""])[0]
    is_correct = node.get("metadata", {}).get("test_question_answer_correct", False)
    # import pdb; pdb.set_trace()

    print(f"{is_correct}: {question_text}:, {user_answer}, ")
    ConsentTestAnswer.objects.create(
        attempt=attempt,
        question_node_id=parent_id,
        question_text=question_text,
        user_answer=user_answer,
        answer_correct=is_correct,
    )

def get_test_results(user, consent_script_version_id):
    """Retrieve the number of correct test responses for a user."""
    return (
        ConsentTestAnswer.objects.filter(
            user=user,
            consent_script_version_id=consent_script_version_id,
            test_try_num=user.num_test_tries,
            answer_correct=True,
        )
        .aggregate(correct_count=Count("answer_correct"))["correct_count"]
        or 0
    )


def process_user_consent(conversation_graph, current_node_id, invite_id):
    node = conversation_graph[current_node_id]["metadata"]

    if node["workflow"] in ["start_consent", "end_consent"]:
        consent_url_obj = ConsentUrl.objects.filter(consent_url=str(invite_id)).first()
        if not consent_url_obj:
            return ''

        user = consent_url_obj.user

        # Check if user is enrolling themselves and hasn't completed consent
        if user.enrolling_myself and not user.consent_complete:
            adult = ConsentAgeGroup.EIGHTEEN_AND_OVER

            Consent.objects.create(
                user=user,
                consent_age_group=adult,
            )

            set_consenting_myself(invite_id, True)
            set_consent_node(invite_id, current_node_id)

            return node.get("enrolling_myself_node_id")

        # Check if enrolling children
        elif user.enrolling_children:
            set_consenting_myself(invite_id, False)

            if get_consenting_children(invite_id) is None:
                set_consenting_children(invite_id, True)
                consent_node_id = get_consent_node(invite_id)
                node = conversation_graph[consent_node_id]["metadata"]
                return node.get("enrolling_children_node_id")

    elif node["workflow"] == "decline_consent":
        consent_url_obj = ConsentUrl.objects.filter(consent_url=str(invite_id)).first()
        if not consent_url_obj:
            return ''

        user = consent_url_obj.user
        user.declined_consent = True
        user.save()

    return ''