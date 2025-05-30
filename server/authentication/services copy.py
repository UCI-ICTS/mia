#!/usr/bin/env python
# authentication/services.py

from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import (
    User,
    FollowUp,
    ConsentUrl,
    Consent,
    ConsentAgeGroup,
    Feedback
)
from authentication.selectors import get_first_test_score, get_latest_consent, get_script_from_invite_id
from utils.cache import set_user_consent_history, set_user_workflow

User = get_user_model()

def retrieve_or_initialize_user_consent(invite_id:str) -> bool:
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


def initialize_consent_history(invite_id, first_sequence):
    """
    Initialize the user consent chat history using the given first sequence.
    """
    history = [{
        "next_consent_sequence": first_sequence,
        "echo_user_response": ""
    }]
    set_user_consent_history(invite_id, history)
    return history


def set_workflow(invite_id, workflow):
    """
    Set the user's workflow in the cache.
    """
    set_user_workflow(invite_id, workflow)


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


class UserInputSerializer(serializers.ModelSerializer):
    script_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['email',
                  'first_name',
                  'last_name',
                  'phone',
                  'password',
                  'is_staff',
                  'is_superuser',
                  'script_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }

    def create(self, validated_data):
        from consentbot.models import ConsentScript

        script_id = validated_data.pop("script_id", None)
        consent_script = None
        if script_id:
            consent_script = ConsentScript.objects.filter(consent_id=script_id).first()

        email = validated_data.get("email")
        username = email.split("@")[0] if email else ""

        password = validated_data.pop("password", None)
        is_staff = validated_data.pop("is_staff", False)
        is_superuser = validated_data.pop("is_superuser", False)

        user = User(
            username=username,
            is_staff=is_staff,
            is_superuser=is_superuser,
            consent_script=consent_script,
            **validated_data
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user
    

class UserOutputSerializer(serializers.ModelSerializer):
    """
    Serializer for User model output.

    This serializer extends the base User model to include additional metadata
    relevant to consent and participation in the study, including:

    - First test score (from ConsentTest)
    - Number of test attempts
    - Whether the user's invite link has expired
    - Consent script name
    - Consent age group
    - Consent creation timestamp

    This serializer is intended to support administrative interfaces that need
    to display both user details and associated consent/test metadata in a
    flattened and frontend-friendly format. It gracefully handles missing data
    for users who may not have completed consent or test participation.

    Note: Staff users will not have consent-related fields populated.
    """
    username = serializers.CharField(read_only=True)
    first_test_score = serializers.SerializerMethodField()
    test_tries = serializers.IntegerField(source='num_test_tries')
    invite_expired = serializers.SerializerMethodField()
    consent_name = serializers.SerializerMethodField()
    consent_age_group = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    script_id = serializers.UUIDField(source='consent_script.consent_id', read_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'is_staff', 'date_joined', 
            'phone', 'consent_name', 'consent_complete', 'first_test_score', 'test_tries',
            'invite_expired', 'consent_age_group', 'created_at', 'script_id' 
        ]

    def get_first_test_score(self, user):
        from authentication.services import get_first_test_score
        return get_first_test_score(user)

    def get_invite_expired(self, user):
        return not user.consent_urls.exists()

    def get_consent_age_group(self, user):
        from authentication.services import get_latest_consent
        consent = get_latest_consent(user)
        if consent and consent.consent_age_group:
            return consent.consent_age_group  
        return None

    def get_consent_name(self, user):
        from authentication.services import get_latest_consent
        consent = get_latest_consent(user)
        if consent and consent.consent_script:
            return consent.consent_script.name
        return None

    def get_created_at(self, user):
        from authentication.services import get_latest_consent
        consent = get_latest_consent(user)
        if consent and consent.created_at:
            return consent.created_at
        return None


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user"""
        email = data.get("email").lower()
        password = data.get("password")
        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password")

        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        if not check_password(data["old_password"], user.password):
            raise serializers.ValidationError({"old_password": "Incorrect password"})

        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match"})

        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        update_last_login(None, instance)
        return instance