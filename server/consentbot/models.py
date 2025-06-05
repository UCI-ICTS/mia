#!/usr/bin/env python
# consentbot/models.py

import uuid
import secrets
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

def default_expiry():
    return timezone.now() + timedelta(weeks=2)


class ConsentAgeGroup(models.TextChoices):
    LESS_THAN_SIX = '<=6', '<=6'
    SEVEN_TO_SEVENTEEN = '7-17', '7-17'
    EIGHTEEN_AND_OVER = '>=18', '>=18'
    EIGHTEEN_AND_OVER_GUARDIANSHIP = '>=18 guardianship', '>=18 guardianship'


class Consent(models.Model):
    user_consent_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE, related_name='consents')
    dependent_user = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_consents')
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


class ConsentScript(models.Model):
    script_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Self-reference for versioning
    derived_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )
    version_number = models.IntegerField()
    script = models.JSONField()

    class Meta:
        unique_together = ('name', 'version_number')

    def __str__(self):
        return f"{self.name} (v{self.version_number})"

    @classmethod
    def get_consent_names(cls):
        return list(cls.objects.values_list('name', flat=True))

    @classmethod
    def get_max_version_number(cls, consent_id):
        max_version = cls.objects.filter(derived_from_id=consent_id).aggregate(
            models.Max('version_number')
        )['version_number__max']
        return max_version if max_version is not None else 0


class ConsentTestAttempt(models.Model):
    attempt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_attempts")
    consent_script_version = models.ForeignKey(ConsentScript, on_delete=models.CASCADE)
    test_try_num = models.IntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)

    def score(self):
        """Return number of correct answers in this attempt."""
        return self.answers.filter(answer_correct=True).count()

    def total_questions(self):
        return self.answers.count()

    def percent_correct(self):
        total = self.total_questions()
        return (self.score() / total) * 100 if total else 0

    def correct_question_ids(self):
        return self.answers.filter(answer_correct=True).values_list("question_node_id", flat=True)
    
    def incorrect_question_ids(self):
        return self.answers.filter(answer_correct=False).values_list("question_node_id", flat=True)


class ConsentTestAnswer(models.Model):
    answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(ConsentTestAttempt, on_delete=models.CASCADE, related_name="answers")
    question_node_id = models.CharField(max_length=64)
    question_text = models.TextField()
    user_answer = models.TextField()
    answer_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)


class ConsentSession(models.Model):
    session_slug = models.SlugField(primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consent_sessions")
    script = models.ForeignKey("ConsentScript", on_delete=models.CASCADE)
    consent = models.ForeignKey(
        "Consent",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True
    )

    # Chat flow state
    current_node = models.CharField(max_length=100)
    visited_nodes = models.JSONField(default=list)   # ["node1", "node2"]
    responses = models.JSONField(default=dict)       # {"node1": {...}, "node2": {...}}
    workflow = models.CharField(max_length=100, blank=True, null=True)
    num_test_tries = models.PositiveIntegerField(default=0)

    # Lifecycle flags
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_session_slug(cls, length=12):
        alphabet = string.ascii_lowercase + string.digits
        while True:
            candidate = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not cls.objects.filter(session_slug=candidate).exists():
                return candidate

    def __str__(self):
        return f"{self.session_slug} ({self.session_slug})"
    
class ConsentChatTurn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey("ConsentSession", on_delete=models.CASCADE, related_name="chat_turns")
    node_id = models.CharField(max_length=32)
    node = models.JSONField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.user} @ {self.node_id} ({self.timestamp.isoformat()})"
    