#!/usr/bin/env python
# authentication/models.py

import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
    consent_script = models.ForeignKey("consentbot.ConsentScript", on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
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

class FollowUp(models.Model):
    user_follow_up_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='user_follow_up')
    follow_up_reason = models.CharField(max_length=200, default='')
    follow_up_info = models.CharField(max_length=200, default='')
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Feedback(models.Model):
    user_feedback_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='user_feedback', blank=True, null=True)
    satisfaction = models.CharField(max_length=25, null=True, blank=True)
    suggestions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
