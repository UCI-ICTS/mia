#!/usr/bin/env python
# authentication/models.py

import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from consentbot.models import ConsentScript

def generate_uuid():
    return uuid.uuid4()

def current_timestamp():
    return timezone.now()

def default_expiry():
    return timezone.now() + timedelta(weeks=2)



class UserManager(BaseUserManager):
    """User Manager
    Custom manager for User model where email is the unique identifier instead of username. 
    """
    def create_user(self, email, password=None, **extra_fields):
    
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # Automatically set username from email prefix
        extra_fields.setdefault("username", email.split("@")[0])

        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    consent_script = models.ForeignKey(ConsentScript, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    consent_complete = models.BooleanField(default=False)
    declined_consent = models.BooleanField(default=False)
    enrolling_myself = models.BooleanField(default=False)
    enrolling_children = models.BooleanField(default=False)
    num_children_enrolling = models.IntegerField(default=0)
    num_test_tries = models.IntegerField(default=1, null=True, blank=True)
    
    # This tells Django to use email as the primary identifier
    USERNAME_FIELD = "email"  
    # Django still requires some fields to be set
    REQUIRED_FIELDS = ["first_name", "last_name"]  
    # Assign the custom manager
    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class UserConsentUrl(models.Model):
    consent_url_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consent_url = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consent_urls')


class UserConsentCache(models.Model):
    key = models.CharField(max_length=200, primary_key=True)
    value = models.TextField()


class UserTest(models.Model):
    user_test_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tests')
    consent_script_version = models.ForeignKey(ConsentScript, on_delete=models.CASCADE, related_name='user_tests')
    test_try_num = models.IntegerField(default=1, null=True, blank=True)
    test_question = models.CharField(max_length=200)
    user_answer = models.CharField(max_length=200)
    answer_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ConsentAgeGroup(models.TextChoices):
    LESS_THAN_SIX = '<=6', '<=6'
    SEVEN_TO_SEVENTEEN = '7-17', '7-17'
    EIGHTEEN_AND_OVER = '>=18', '>=18'
    EIGHTEEN_AND_OVER_GUARDIANSHIP = '>=18 guardianship', '>=18 guardianship'


class UserConsent(models.Model):
    user_consent_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_consents')
    dependent_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_consents')
    consent_script = models.ForeignKey("consentbot.ConsentScript", on_delete=models.CASCADE, related_name="user_consents", null=True, blank=True)
    consent_age_group = models.CharField(max_length=20, choices=ConsentAgeGroup.choices)
    store_sample_this_study = models.BooleanField(default=True)
    store_sample_other_studies = models.BooleanField(default=False)
    store_phi_this_study = models.BooleanField(default=True)
    store_phi_other_studies = models.BooleanField(default=False)
    return_primary_results = models.BooleanField(default=False)
    return_actionable_secondary_results = models.BooleanField(default=False)
    return_secondary_results = models.BooleanField(default=False)
    consent_statements = models.TextField(default='')
    user_full_name_consent = models.CharField(max_length=200, default='')
    child_full_name_consent = models.CharField(max_length=200, null=True, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserFollowUp(models.Model):
    user_follow_up_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_follow_up')
    follow_up_reason = models.CharField(max_length=200, default='')
    follow_up_info = models.CharField(max_length=200, default='')
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class UserFeedback(models.Model):
    user_feedback_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_feedback')
    satisfaction = models.CharField(max_length=25, null=True, blank=True)
    suggestions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
