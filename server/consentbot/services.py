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
    ConsentSession,
)
from consentbot.selectors import (
    build_chat_from_history,
    format_turn,
    get_script_from_session_slug,
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
        invite = ConsentSession.objects.filter(user=user).order_by('-created_at').first()
        if not invite:
            raise serializers.ValidationError("No invite URL found for this user.")

        # 🔍 Lookup the ConsentScript based on the invite
        consent_script = get_script_from_session_slug(invite.session_slug)

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
    session_slug = serializers.CharField(
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


class ConsentSessionInputSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)

    class Meta:
        model = ConsentSession
        fields = ['username']

    def create(self, validated_data):
        username = validated_data.pop('username')
        user = User.objects.get(username=username)
        script_id = user.consent_script.script_id

        return ConsentSession.objects.create(
            user=user,
            script_id=script_id,
            session_slug=ConsentSession.generate_session_slug(),
            **validated_data
        )


class ConsentSessionOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    invite_link = serializers.SerializerMethodField()

    class Meta:
        model = ConsentSession
        fields = [
            'session_slug',
            'session_slug',
            'invite_link',
            'created_at',
            'expires_at',
            'user_id',
            'email',
        ]

    def get_invite_link(self, obj):
        base_url = getattr(settings, 'PUBLIC_HOSTNAME', 'https://genomics.icts.uci.edu')
        return f"{base_url}/consent/{obj.session_slug}/"


def clean_up_after_chat(session_slug):
    """Set the invite URL to expire 24 hours from now."""
    try:
        session_slug = ConsentSession.objects.get(session_slug=str(session_slug))
        session_slug.expires_at = timezone.now() + datetime.timedelta(hours=24)
        session_slug.save()
    except ConsentSession.DoesNotExist:
        # Log or raise if needed
        pass


def get_or_initialize_consent_history(session_slug):
    """
    Retrieve existing consent history for a given session_slug,
    or initialize it with the starting node and first chat sequence.

    Returns:
        tuple: (history, just_created)
    """

    history = get_user_consent_history(session_slug)
    if history:
        return history, False

    graph = get_script_from_session_slug(session_slug)
    start_node = get_consent_start_id(graph)
    sequence = process_consent_sequence(start_node, session_slug, graph=graph)

    history = [format_turn(graph, start_node, echo_user_response="", next_sequence=sequence)]
    set_user_consent_history(session_slug, history)
    return history, True


def get_or_initialize_user_consent(session_slug:str) -> bool:
    """
    Given a session_slug, retrieve the existing Consent or initialize one.

    Returns:
        tuple: (Consent instance, bool indicating if it was created)
    """
    # Get the ConsentSession instance (or 404 if invalid/expired)
    invite = get_object_or_404(ConsentSession, session_slug=session_slug)
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
    session_slug: str,
    graph: Optional[dict] = None
) -> dict:
    """
    Process the next step in the consent chat graph from a given node.

    This retrieves the next bot message sequence and updates the cached
    workflow state by removing nodes that have already been visited.

    Args:
        node_id (str): The node to begin traversal from.
        session_slug (str): The session ID (usually a UUID) identifying the consent URL.
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
        graph = get_script_from_session_slug(session_slug)
    node = graph.get(node_id, {})

    # Handle second test attempt traversal
    if (
        node.get("type") == "bot"
        and node.get("metadata", {}).get("workflow") == "test_user_understanding"
        # and node.get("metadata", {}).get("test_question") is True
    ):
        user = ConsentSession.objects.get(session_slug=session_slug).user
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
    workflow = get_user_workflow(session_slug)
    if workflow and workflow[0] and node_id in workflow[0]:
        workflow[0] = [n for n in workflow[0] if n not in sequence["visited"]]
        if not workflow[0] or sequence["end"]:
            workflow.pop(0)
        set_user_workflow(session_slug, workflow)

    return sequence


def append_chat_history(session_slug:str, chat_turn:dict):
    """
    Appends a chat turn to the user's consent chat history in cache.

    Args:
        session_slug (str): The invite UUID identifying the session.
        chat_turn (dict): A formatted chat turn dictionary using `format_turn`.
    """
    history = get_user_consent_history(session_slug)
    history.append(chat_turn)
    set_user_consent_history(session_slug, history)


def update_consent_and_advance(session_slug, node_id, graph, echo_user_response):
    if node_id not in graph:
        return [{"messages": [f"Invalid node: {node_id}"], "responses": []}]
    next_node_id = graph[node_id]["child_ids"][0]
    next_sequence = process_consent_sequence(next_node_id, session_slug)
    history = get_user_consent_history(session_slug)

    history.append(format_turn(graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(session_slug, history)
    clean_up_after_chat(session_slug)

    return build_chat_from_history(session_slug)


def handle_sample_storage(graph, session_slug, responses):
    """
    Processes the 'sample storage' form by updating the user's consent record,
    saving chat state, and progressing the conversation.

    Args:
        conversation_graph (dict): The full consent script graph.
        session_slug (str): The invite UUID identifying the session.
        responses (list): List of form response dicts.

    Returns:
        list[dict]: Updated chat history for the frontend.
    """

    samples, node_id = responses[0]['value'], responses[1]['value']
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.store_sample_this_study = True
    consent.store_sample_other_studies = (samples == "storeSamplesOtherStudies")
    consent.save()
    return update_consent_and_advance(session_slug, node_id, graph, "Sample use submitted!")


def handle_phi_use(graph, session_slug, responses):
    """
    Handles the form submission for PHI (Protected Health Information) usage consent.

    Updates the user's `Consent` object to reflect their PHI usage choices and 
    appends the next sequence of the chat to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        session_slug (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    samples, node_id = responses[0]['value'], responses[1]['value']
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.store_phi_this_study = True
    consent.store_phi_other_studies = (samples == "storePhiOtherStudies")
    consent.save()
    return update_consent_and_advance(session_slug, node_id, graph, "PHI use submitted!")


def handle_result_return(graph, session_slug, responses):
    """
    Handles the form submission for return of genetic results preferences.

    Updates the user's `Consent` object with their selected options and appends
    the next chat turn to the user history.

    Args:
        conversation_graph (dict): The parsed consent script.
        session_slug (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    response_dict = {r["name"]: r["value"] for r in responses}
    node_id = response_dict["node_id"]
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.return_primary_results = response_dict.get("rorPrimary") is True
    consent.return_actionable_secondary_results = response_dict.get("rorSecondary") is True
    consent.return_secondary_results = response_dict.get("rorSecondaryNot") is True
    consent.save()
    return update_consent_and_advance(session_slug, node_id, graph, "Result return preferences submitted!")


def handle_consent(graph, session_slug, responses):
    """
    Handles the final user consent form submission.

    Stores the user's name, timestamps the consent, and marks the consent
    as complete. Also updates chat history with the next sequence.

    Args:
        conversation_graph (dict): The parsed consent script.
        session_slug (str): UUID of the invite link.
        responses (list): List of form responses submitted by the user.

    Returns:
        list: Updated chat history to be sent back to the frontend.
    """

    response_dict = {r["name"]: r["value"] for r in responses}
    node_id = response_dict["node_id"]
    user = ConsentSession.objects.get(session_slug=session_slug).user
    consent = Consent.objects.filter(user=user).latest('created_at')

    if response_dict.get("consent"):
        consent.user_full_name_consent = response_dict.get("fullname", "")
        consent.consented_at = timezone.now()
        user.consent_complete = True
        user.save()
        consent.save()

    return update_consent_and_advance(session_slug, node_id, graph, "Consent submitted!")


def handle_family_enrollment_form(conversation_graph, session_slug, responses):
    """
    Processes the form where a user selects who they are enrolling (self, children, or both).
    Updates user flags, generates dynamic workflow, and advances the chat sequence.
    """
    checked = responses[0]["value"]
    user = ConsentSession.objects.get(session_slug=session_slug).user
    history = get_user_consent_history(session_slug)
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
    generate_workflow(start_node_id, workflow_ids, session_slug)
    next_sequence = process_consent_sequence(start_node_id, session_slug)

    history.append(format_turn(conversation_graph, start_node_id, ", ".join(checked), next_sequence))
    set_user_consent_history(session_slug, history)

    return build_chat_from_history(session_slug)


def handle_user_feedback_form(graph, session_slug, responses):
    """
    Handles submission of a feedback form, stores the data,
    and advances the chat sequence.

    Args:
        session_slug (str): The invite UUID identifying the session.
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

    user = ConsentSession.objects.get(session_slug=session_slug).user
    if data.get("anonymize") is None:
        payload["user"] = user.pk

    serializer = FeedbackInputSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return update_consent_and_advance(session_slug, node_id, graph, "Feedback submitted!")


def handle_other_adult_contact_form(conversation_graph, session_slug, responses):
    """
    Processes the form submission where the user wants to refer another adult.
    This creates a new user record and progresses the chat.

    Args:
        conversation_graph (dict): Parsed consent script graph.
        session_slug (str): The invite UUID.
        responses (list): Submitted form responses.

    Returns:
        list[dict]: Updated chat history for frontend.
    """
    response_dict = {r.get("name"): r.get("value") for r in responses if r.get("name")}
    node_id = response_dict.get("node_id")

    session_slug = get_object_or_404(ConsentSession, session_slug=session_slug)
    referring_user = session_slug.user

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
    next_sequence = process_consent_sequence(next_node_id, session_slug)

    history = get_user_consent_history(session_slug)
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(session_slug, history)

    return build_chat_from_history(session_slug)


def generate_workflow(start_node_id, user_option_node_ids, session_slug):
    conversation_graph = get_script_from_session_slug(session_slug)

    # generate a sub workflow to dynamically process user responses
    workflow = get_user_workflow(session_slug)

    metadata_field = conversation_graph[start_node_id]['metadata']['workflow']
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(conversation_graph, user_option_node_id, metadata_field)
        workflow.append(sub_graph)
    set_user_workflow(session_slug, workflow)
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


def process_test_question(conversation_graph, current_node_id, session_slug):
    node_metadata = conversation_graph.get(current_node_id, {}).get("metadata", {})
    
    if node_metadata.get("workflow") != "test_user_understanding":
        return ''

    try:
        # Get user and script
        session_slug = get_object_or_404(ConsentSession, session_slug=str(session_slug))
        user = session_slug.user
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

    except ConsentSession.DoesNotExist:
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


def process_user_consent(conversation_graph, current_node_id, session_slug):
    node = conversation_graph[current_node_id]["metadata"]

    if node["workflow"] in ["start_consent", "end_consent"]:
        session_slug_obj = ConsentSession.objects.filter(session_slug=str(session_slug)).first()
        if not session_slug_obj:
            return ''

        user = session_slug_obj.user

        # Check if user is enrolling themselves and hasn't completed consent
        if user.enrolling_myself and not user.consent_complete:
            adult = ConsentAgeGroup.EIGHTEEN_AND_OVER

            Consent.objects.create(
                user=user,
                consent_age_group=adult,
            )

            set_consenting_myself(session_slug, True)
            set_consent_node(session_slug, current_node_id)

            return node.get("enrolling_myself_node_id")

        # Check if enrolling children
        elif user.enrolling_children:
            set_consenting_myself(session_slug, False)

            if get_consenting_children(session_slug) is None:
                set_consenting_children(session_slug, True)
                consent_node_id = get_consent_node(session_slug)
                node = conversation_graph[consent_node_id]["metadata"]
                return node.get("enrolling_children_node_id")

    elif node["workflow"] == "decline_consent":
        session_slug_obj = ConsentSession.objects.filter(session_slug=str(session_slug)).first()
        if not session_slug_obj:
            return ''

        user = session_slug_obj.user
        user.declined_consent = True
        user.save()

    return ''