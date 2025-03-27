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
    UserFollowUp,
    UserConsentUrl,
    UserConsent,
    ConsentAgeGroup
)
from authentication.selectors import get_first_test_score, get_latest_consent
from utils.cache import set_user_consent_history, set_user_workflow


User = get_user_model()

def retrieve_or_initialize_user_consent(invite_id):
    """
    Given an invite ID (UUID), retrieve the existing UserConsent or initialize one.

    Returns:
        tuple: (UserConsent instance, bool indicating if it was created)
    """
    # Get the UserConsentUrl instance (or 404 if invalid/expired)
    invite = get_object_or_404(UserConsentUrl, consent_url=invite_id)

    # Check for an existing UserConsent record
    existing = UserConsent.objects.filter(user=invite.user, dependent_user=None).order_by('-created_at').first()

    if existing:
        return existing, False

    # Otherwise, create a new UserConsent (with placeholder values)
    new_consent = UserConsent.objects.create(
        user=invite.user,
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


class UserConsentInputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    dependent_user_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = UserConsent
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
        import pdb; pdb.set_trace()
        invite = UserConsentUrl.objects.filter(user=user).order_by('-created_at').first()
        if not invite:
            raise serializers.ValidationError("No invite URL found for this user.")

        # 🔍 Lookup the ConsentScript based on the invite
        consent_script = get_script_from_invite_id(invite.consent_url)

        return UserConsent.objects.create(
            user=user,
            dependent_user=dependent_user,
            consent_script=consent_script,
            **validated_data
        )


class UserConsentOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    dependent_user_id = serializers.UUIDField(source='dependent_user.user_id', read_only=True)
    dependent_email = serializers.EmailField(source='dependent_user.email', read_only=True)

    class Meta:
        model = UserConsent
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


class UserUserFollowUpInputSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta: 
        model = UserFollowUp
        fields = ['email', 'follow_up_reason', 'follow_up_info']  # exclude 'user', 'resolved', etc.

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with that email.")

        follow_up = UserFollowUp.objects.create(user=user, **validated_data)
        return follow_up


class UserUserFollowUpOutputSerializer(serializers.ModelSerializer):
    class Meta: 
        model = UserFollowUp
        fields = [
            'user_follow_up_id',
            'follow_up_reason',
            'follow_up_info',
            'resolved',
            'created_at',
            'user'  # keep this here so DRF knows it's related, we'll override it below
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = instance.user

        # Flatten user fields into the top level
        data['user_id'] = user.user_id
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['email'] = user.email
        data['phone'] = user.phone

        # Optionally remove the nested user field if you don’t want it
        data.pop('user', None)

        return data


class UserConsentUrlInputSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)

    class Meta:
        model = UserConsentUrl
        fields = ['username']

    def create(self, validated_data):
        from authentication.models import User

        username = validated_data.pop('username')
        user = User.objects.get(username=username)

        return UserConsentUrl.objects.create(user=user, **validated_data)


class UserConsentUrlOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    invite_link = serializers.SerializerMethodField()

    class Meta:
        model = UserConsentUrl
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
        base_url = getattr(settings, 'CONSENT_INVITE_BASE_URL', 'https://genomics.icts.uci.edu')
        return f"{base_url}/consent/{obj.consent_url}/"


class UserInputSerializer(serializers.ModelSerializer):
    consent_script_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['email',
                  'first_name',
                  'last_name',
                  'phone',
                  'password',
                  'is_staff',
                  'is_superuser',
                  'consent_script_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }

    def create(self, validated_data):
        from consentbot.models import ConsentScript

        consent_script_id = validated_data.pop("consent_script_id", None)
        consent_script = None
        if consent_script_id:
            consent_script = ConsentScript.objects.filter(consent_id=consent_script_id).first()

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

    - First test score (from UserTest)
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
    consent_script_id = serializers.UUIDField(source='consent_script.consent_id', read_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'is_staff', 'date_joined', 
            'phone', 'consent_name', 'consent_complete', 'first_test_score', 'test_tries',
            'invite_expired', 'consent_age_group', 'created_at', 'consent_script_id' 
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