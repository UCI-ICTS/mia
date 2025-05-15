#!/usr/bin/env python
# authentication/services.py

from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model, authenticate
from authentication.models import (
    User,
    Feedback,
    FollowUp
)
from consentbot.models import ConsentScript
from consentbot.selectors import get_user_from_invite_id, get_latest_consent

User = get_user_model()


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
        request = self.context.get("request")
        referring_user = request.user if request and request.user.is_authenticated else None

        script_id = validated_data.pop("script_id", None)
        consent_script = None
        if script_id:
            consent_script = ConsentScript.objects.filter(script_id=script_id).first()

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
            referred_by=referring_user,
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
        test = user.user_tests.order_by("created_at").first()
        return test.score if test else "NA"

    def get_invite_expired(self, user):
        return not user.consent_urls.exists()

    def get_consent_age_group(self, user):
        consent = get_latest_consent(user)
        if consent and consent.consent_age_group:
            return consent.consent_age_group  
        return None

    def get_consent_name(self, user):
        consent = get_latest_consent(user)
        if consent and consent.consent_script:
            return consent.consent_script.name
        return None

    def get_created_at(self, user):
        consent = get_latest_consent(user)
        if consent and consent.created_at:
            return consent.created_at
        return None


class FollowUpInputSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta: 
        model = FollowUp
        fields = ['email', 'follow_up_reason', 'follow_up_info']  # exclude 'user', 'resolved', etc.

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with that email.")

        follow_up = FollowUp.objects.create(user=user, **validated_data)
        return follow_up


class FollowUpOutputSerializer(serializers.ModelSerializer):
    class Meta: 
        model = FollowUp
        fields = [
            'user_follow_up_id',
            'follow_up_reason',
            'follow_up_info',
            'resolved',
            'created_at',
            'user'  # required for DRF relation mapping
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

        # Add consent script details if available
        if user.consent_script:
            data['consent_script_id'] = str(user.consent_script.script_id)
            data['consent_script_name'] = user.consent_script.name
            data['consent_script_version'] = user.consent_script.version_number
        else:
            data['consent_script_id'] = None
            data['consent_script_name'] = None
            data['consent_script_version'] = None

        # Remove nested user field
        data.pop('user', None)


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


class FeedbackInputSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Feedback
        fields = ["user", "satisfaction", "suggestions"]


class FeedbackOutputSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "user_feedback_id",
            "user_id",
            "satisfaction",
            "suggestions",
            "created_at",
        ]
    def get_user_id(self, obj):
            return str(obj.user.pk) if obj.user else None

def create_follow_up_with_user(invite_id, reason, more_info):
    """Create a follow-up entry for a user."""
    user = get_user_from_invite_id(invite_id)

    serializer = FollowUpInputSerializer(
        data={
            "email": user.email,
            "follow_up_reason": reason,
            "follow_up_info": more_info
        }
    )
    serializer.is_valid(raise_exception=True)
    return serializer.save()