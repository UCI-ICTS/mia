#!/usr/bin/env python
# consentbot/services.py

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from typing import Optional

from authentication.services import FeedbackInputSerializer, create_follow_up_with_user
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
    traverse_consent_graph,
    get_consent_start_id,
    get_user_label,
    get_next_retry_question_node,
)

from utils.cache import (
    get_user_consent_history,
    set_user_consent_history,
    append_to_consent_history
) 

User = get_user_model()  
# flags
TEST_QUESTIONS_CORRECT = 10
NUM_TEST_TRIES = 2

class RenderBlockSerializer(serializers.Serializer):
    """
    Describes the next UI input block the frontend should render.

    This structure is separate from chat history. It represents the current
    actionable form or button set that should be presented to the user.

    Example:
        {
            "type": "form",
            "fields": [
                {"name": "age", "label": "Your age", "type": "number"}
            ]
        }

    Fields:
        - type: Specifies the type of UI block ("form" or "button").
        - fields: A list of field configuration dictionaries. Required for forms.
    """
    type = serializers.ChoiceField(choices=["form", "button"])
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
            'invite_link',
            'created_at',
            'expires_at',
            'user_id',
            'email',
        ]

    def get_invite_link(self, obj):
        base_url = getattr(settings, 'PUBLIC_HOSTNAME', 'https://genomics.icts.uci.edu')
        return f"{base_url}/consent/{obj.session_slug}/"


def mark_session_for_expiration(session_slug):
    """Set a session to expire 24 hours from now.
    
    Call when    
        At the end of the conversation (final node)
        After consent is submitted or declined
        After feedback is submitted
        Or after N minutes of inactivity (future: background job)
    """
    try:
        session = ConsentSession.objects.get(session_slug=session_slug)
        session.expires_at = timezone.now() + timedelta(hours=24)
        session.save(update_fields=["expires_at"])
    except ConsentSession.DoesNotExist:
        pass  # TODO: Or log


def get_or_initialize_user_consent(session_slug: str) -> tuple[Consent, bool]:
    """
    Given a session_slug, retrieve the existing Consent or initialize one.

    Returns:
        tuple: (Consent instance, bool indicating if it was created)
    """
    session = get_object_or_404(ConsentSession, session_slug=session_slug)

    # Try to use the session.consent directly if already linked
    if session.consent:
        return session.consent, False

    # Fallback to latest consent object
    consent = Consent.objects.filter(
        user=session.user,
        dependent_user=None
    ).order_by('-created_at').first()
    
    if consent:
        session.consent = consent
        session.save(update_fields=["consent"])
        return consent, False

    # Otherwise, create and link a new Consent
    new_consent = Consent.objects.create(
        user=session.user,
        consent_script=session.script,
        consent_age_group=ConsentAgeGroup.EIGHTEEN_AND_OVER
    )
    session.consent = new_consent
    session.save(update_fields=["consent"])

    return new_consent, True


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

    graph = get_script_from_session_slug(invite_id)
    start_node = get_consent_start_id(graph)
    sequence = traverse_consent_graph(graph, start_node)

    # Use full chat_turns list (already formatted)
    history = sequence["chat_turns"]
    set_user_consent_history(invite_id, history)
    return history, True


def update_consent_and_advance(session_slug, node_id, graph, user_reply: str):
    """
    Updates consent state and advances to the next node in the graph.

    Args:
        session_slug (str): The session identifier.
        node_id (str): The current node ID the user responded to.
        graph (dict): The full conversation graph.
        user_reply (str): The visible text from the user's choice/form.

    Returns:
        list: Full updated chat history.
    """
    if node_id not in graph:
        return [{"messages": ["Invalid node: {node_id}"], "responses": []}]

    next_node_id = graph[node_id]["child_ids"][0]

    user_turn = format_turn(
        graph=graph,
        speaker="user",
        node_id=node_id,
        messages=[user_reply]
    )

    append_to_consent_history(session_slug, user_turn)
    
    bot_block = get_next_chat_block(next_node_id, session_slug, graph=graph)
    for turn in bot_block["chat_turns"]:
        append_to_consent_history(session_slug, turn)

    return build_chat_from_history(session_slug)


def handle_sample_storage(graph, session_slug, responses):
    data = {r["name"]: r["value"] for r in responses}
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.store_sample_this_study = True
    consent.store_sample_other_studies = (data.get("storeSamplesOtherStudies") == "yes")
    consent.save()

    return update_consent_and_advance(session_slug, data["node_id"], graph, "Sample use submitted!")


def handle_phi_use(graph, session_slug, responses):
    data = {r["name"]: r["value"] for r in responses}
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.store_phi_this_study = True
    consent.store_phi_other_studies = (data.get("storePhiOtherStudies") == "yes")
    consent.save()

    return update_consent_and_advance(session_slug, data["node_id"], graph, "PHI use submitted!")


def handle_result_return(graph, session_slug, responses):
    response_dict = {r["name"]: r["value"] for r in responses}
    node_id = response_dict["node_id"]
    consent = Consent.objects.filter(user=ConsentSession.objects.get(session_slug=session_slug).user).latest('created_at')
    consent.return_primary_results = (response_dict.get("rorPrimary") == "yes")
    consent.return_actionable_secondary_results = (response_dict.get("rorSecondary") == "yes")
    consent.return_secondary_results = (response_dict.get("rorSecondaryNot") == "yes")
    consent.save()

    return update_consent_and_advance(session_slug, node_id, graph, "Result return preferences submitted!")


def handle_consent(graph, session_slug, responses):
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


def handle_family_enrollment_form(graph, session_slug, responses):
    """
    Handles the family enrollment form with checkbox inputs.
    Updates user flags and walks all selected enrollment paths.

    Args:
        graph (dict): The chat graph
        session_slug (str): User's session slug
        responses (list): List of submitted checkbox selections

    Returns:
        list: Updated chat history
    """
    user = ConsentSession.objects.get(session_slug=session_slug).user
    history = get_user_consent_history(session_slug)
    parent_node_id = history[-1]["node_id"] if history else None
    if not parent_node_id or parent_node_id not in graph:
        raise ValueError("Invalid or missing parent node in history.")

    checked_items = responses[0].get("value", [])
    if not isinstance(checked_items, list):
        raise ValueError("Expected list of checked items from response.")

    try:
        field_map = {
            f["name"]: f["id_value"]
            for f in history[-1]["responses"][0]["label"]["fields"]
        }
    except (KeyError, IndexError, TypeError):
        raise ValueError("Checkbox field structure invalid or missing from chat history.")

    seen = set()
    for item in checked_items:
        node_id = field_map.get(item)
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)

        if item == "myself":
            user.enrolling_myself = True
        elif item == "myChildChildren":
            user.enrolling_children = True

        user_turn = format_turn(
            graph=graph,
            speaker="user",
            node_id=node_id,
            messages=[item],
            timestamp=timezone.now().isoformat()
        )
        append_to_consent_history(session_slug, user_turn)

        bot_block = get_next_chat_block(node_id, session_slug, graph=graph)

        for turn in bot_block["chat_turns"]:
            append_to_consent_history(session_slug, turn)

    user.save()
    return get_user_consent_history(session_slug)


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
    next_sequence = get_next_chat_block(next_node_id, session_slug)

    history = next_sequence["chat_turns"]
    # TODO Fix this
    import pdb; pdb.set_trace()
    history.append(format_turn(conversation_graph, node_id, echo_user_response, next_sequence))
    set_user_consent_history(session_slug, history)

    return build_chat_from_history(session_slug)


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
        session = get_object_or_404(ConsentSession, session_slug=str(session_slug))
        user = session.user
        script_version = getattr(user, "consent_script", None)
        if not script_version:
            return node_metadata.get("fail_node_id", "")

        # Start or retrieve the current test attempt
        attempt, _ = ConsentTestAttempt.objects.get_or_create(
            user=user,
            consent_script_version=script_version,
        )

        # Save this question/response to the attempt
        is_correct = save_test_question(conversation_graph, current_node_id, attempt)
        eval_id = get_next_retry_question_node(attempt)
        
        # Wrong answer on retry? Evaluate
        if is_correct is False and user.num_test_tries == 2:
            return evaluate_attempt(user, attempt, conversation_graph)
        
        # Retry complete? Evaluate
        if user.num_test_tries == 2 and eval_id is None:
            return evaluate_attempt(user, attempt, conversation_graph)
        
        # Final question? Evaluate
        if node_metadata.get("end_sequence") is True:
            return evaluate_attempt(user, attempt, conversation_graph)

    except ConsentSession.DoesNotExist:
        return node_metadata.get("fail_node_id", "")
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing test question: {e}")
        return node_metadata.get("fail_node_id", "")

    return ''


def evaluate_attempt(user, attempt, conversation_graph):
    """
    Evaluates a user's test attempt and determines the next node in the consent chat.

    This function:
    - Scans the entire graph for nodes with the `test_user_understanding` workflow.
    - Collects `pass_node_id`, `retry_node_id`, and `fail_node_id` from metadata.
    - Evaluates the test score and returns the appropriate next node ID.

    Args:
        user (User): The user taking the test.
        attempt (ConsentTestAttempt): The attempt object containing answers.
        conversation_graph (dict): Full graph structure of the consent script.

    Returns:
        str: Node ID for the next step in the consent flow.
    """
    pass_nodes = []
    retry_nodes = []
    fail_nodes = []

    for node in conversation_graph.values():
        metadata = node.get("metadata", {})
        if metadata.get("workflow") == "test_user_understanding":
            if "pass_node_id" in metadata:
                pass_nodes.append(metadata["pass_node_id"])
            if "retry_node_id" in metadata:
                retry_nodes.append(metadata["retry_node_id"])
            if "fail_node_id" in metadata:
                fail_nodes.append(metadata["fail_node_id"])

    test_result = len(attempt.correct_question_ids())

    if test_result < TEST_QUESTIONS_CORRECT:
        if user.num_test_tries < NUM_TEST_TRIES:
            user.num_test_tries += 1
            user.save(update_fields=["num_test_tries"])
            return retry_nodes[0] if retry_nodes else ""
        else:
            return fail_nodes[0] if fail_nodes else ""
    else:
        return pass_nodes[0] if pass_nodes else ""


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
    return is_correct

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


def handle_user_step(session_slug: str, node_id: str, graph: dict) -> list[dict]:
    """
    Handle a user's response in the consent chat by:
    - Determining the next node based on workflow
    - Recording the user's reply as a chat turn
    - Getting the next bot response
    - Saving both turns to the chat history and updating session metadata

    Args:
        session_slug (str): Unique identifier for the chat session
        node_id (str): The ID of the user-submitted node
        graph (dict): The full conversation graph

    Returns:
        list[dict]: Updated full chat history
    """
    next_node_id = None
    node = graph.get(node_id, {})
    metadata = node.get("metadata", {})
    workflow = metadata.get("workflow", "")
    session = ConsentSession.objects.get(session_slug=session_slug)

    # Determine next node in the graph
    if workflow == "test_user_understanding":
        next_node_id = process_test_question(graph, node_id, session_slug)
    elif workflow in ["start_consent", "decline_consent"]:
        next_node_id = process_user_consent(graph, node_id, session_slug)
    elif workflow == "follow_up":
        create_follow_up_with_user(
            session_slug,
            metadata.get("follow_up_reason", ""),
            metadata.get("follow_up_info", "")
        )
    if not next_node_id:
        next_node_id = graph[node_id].get("child_ids", [None])[0]
    # Format and store user turn
    user_label = get_user_label(node) if node.get("type") == "user" else ""
    user_turn = format_turn(
        graph=graph,
        speaker="user",
        node_id=node_id,
        messages=[user_label]
    )
    append_to_consent_history(session_slug, user_turn)
    
    
    # Return user + bot turn history
    bot_turns = get_next_chat_block(next_node_id, session_slug, graph=graph)

    for turn in bot_turns["chat_turns"]:
        append_to_consent_history(session_slug, turn)

    # Update session metadata
    session.current_node = bot_turns["chat_turns"][-1]["node_id"] if bot_turns else next_node_id
    if session.current_node not in session.visited_nodes:
        session.visited_nodes.append(session.current_node)
    session.responses[node_id] = user_label
    session.save(update_fields=["current_node", "visited_nodes", "responses"])
    
    return get_user_consent_history(session_slug)

def process_user_consent(graph: dict, node_id: str, session_slug: str) -> Optional[str]:
    """
    Process a user consent step, including branching for adult vs child workflows or declined consent.

    Args:
        graph (dict): The full consent conversation graph.
        node_id (str): The ID of the user-submitted node.
        session_slug (str): The current consent session identifier.

    Returns:
        Optional[str]: The next node ID to traverse, if any.
    """
    metadata = graph.get(node_id, {}).get("metadata", {})
    workflow = metadata.get("workflow", "")
    session = ConsentSession.objects.select_related("user").get(session_slug=session_slug)
    user = session.user
    consent = session.consent
    if not consent:
        raise ValueError("Consent object is missing for user.")

    if workflow in ["start_consent", "end_consent"]:

        # Self-consent path
        if user.enrolling_myself and not user.consent_complete:
            consent.consent_age_group = ConsentAgeGroup.EIGHTEEN_AND_OVER
            consent.save(update_fields=["consent_age_group"])
            user.consent_complete = True
            user.save(update_fields=["consent_complete"])

            # Follow the next node defined for self-enrollment
            return metadata.get("enrolling_myself_node_id")

        # Child consent path
        elif user.enrolling_children:
            # Consent for children is handled in a later part of the graph
            return metadata.get("enrolling_children_node_id")

    elif workflow == "decline_consent":
        user.declined_consent = True
        user.save(update_fields=["declined_consent"])

    # No next step defined — return empty string to indicate end of path
    return ""


def get_next_chat_block(
    node_id: str,
    session_slug: str,
    graph: Optional[dict] = None
) -> dict:
    """
    Given a node_id, retrieve the next bot message sequence and user response options,
    traversing the graph until a user prompt or end node is reached.

    Args:
        node_id (str): The starting node ID in the graph
        session_slug (str): Unique identifier for the user's session
        graph (dict, optional): The preloaded graph (optional; loads from session if not provided)

    Returns:
        dict: A structured response containing:
            - "chat_turns": List of bot message turns
            - "responses": List of user response options
            - "render": Optional render config
            - "end": Whether this is an end sequence
            - "visited": Node IDs traversed in this sequence
    """
    if graph is None:
        graph = get_script_from_session_slug(session_slug)
    if node_id not in graph:
        raise ValueError(f"Node {node_id} not found in graph.")

    return traverse_consent_graph(graph, node_id, session_slug)


def get_consent_session_or_error(session_slug: str) -> ConsentSession:
    """
    Retrieve a ConsentSession by slug or raise a ValueError.
    Args:
        session_slug (str): The session identifier slug.

    Returns:
        ConsentSession: The matching session object.

    Raises:
        ValueError: If no session is found.
    """
    #TODO extend it to check is_active, expires_at
    try:
        return ConsentSession.objects.get(session_slug=session_slug)
    except ConsentSession.DoesNotExist:
        raise ValueError(f"No session found for slug: {session_slug}")


def handle_form_submission(data):
    """
    Process a submitted form during the consent chat flow.

    Args:
        data (dict): Validated data from ConsentResponseInputSerializer

    Returns:
        tuple: (history list, render dict)
    """

    session_slug = str(data["session_slug"])
    form_type = data["form_type"]
    responses = data["form_responses"] + [{"name": "node_id", "value": data["node_id"]}]
    graph = get_script_from_session_slug(session_slug)

    handler = FORM_HANDLER_MAP.get(form_type)
    if not handler:
        raise ValueError(f"Unknown form_type: {form_type}")

    history = handler(graph, session_slug, responses)

    render = history[-1]['render']
    
    return history, render

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