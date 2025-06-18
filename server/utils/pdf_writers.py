#!/usr/bin/env python
# utils/pdf_writers.py

from datetime import datetime
import os
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model
from consentbot.models import Consent, ConsentSession

User = get_user_model()


def generate_consent_pdf(consent, output_pdf_path):
    """
    Generate a filled PDF of the static consent form with participant responses.

    Args:
        consent (Consent): The Consent model instance.
        output_pdf_path (str): Full path where the PDF should be saved.
    """
    user = consent.user
    
    data_dict = {
        "record_id": str(consent.user_consent_id),
        "study_id": "UCI GREGoR",
        "pmgrc_id": f"{user.last_name}, {user.first_name}",
        "date_of_birth": user.date_joined.strftime("%m/%d/%Y"),
        "participant_first_name": user.first_name,
        "participant_last_name": user.last_name,
        "first_name": " ",
        "last_name": " ",
        "signature": consent.user_full_name_consent,
        "representative": " ",
        "datetime_now": datetime.now().strftime("%m/%d/%Y %I:%M %p"),
        "store_sample_other_studies": consent.store_sample_other_studies,
        "store_phi_other_studies": consent.store_phi_other_studies,
        "return_primary_results": consent.return_primary_results,
        "return_actionable_secondary_results": consent.return_actionable_secondary_results,
        "return_secondary_results": consent.return_secondary_results,
        "statement": consent.consent_statements,
    }
    
    if consent.guardian:
        gaurdian = consent.guardian
        data_dict["first_name"] = gaurdian.first_name
        data_dict["last_name"] = gaurdian.last_name
        data_dict["representative"] = f"{gaurdian.first_name} {gaurdian.last_name}"

    html_content = render_to_string("consent_form.html", data_dict)
    HTML(string=html_content).write_pdf(output_pdf_path)


def generate_transcript_pdf(session, output_pdf_path):
    """
    Generate a transcript-style PDF of the chat interaction during a consent session.

    Args:
        session (ConsentSession): The ConsentSession object.
        output_pdf_path (str): Full path where the PDF should be saved.
    """
    chat_turns = session.chat_turns.all().select_related("session", "user")

    context = {
        "chat_turns": chat_turns,
        "first_name": session.user.first_name,
        "last_name": session.user.last_name,
        "datetime_now": datetime.now().strftime("%m/%d/%Y"),
    }

    import pdb; pdb.set_trace()
    html_content = render_to_string("chat_transcript.html", context)
    HTML(string=html_content).write_pdf(output_pdf_path)


def main():
    user = User.objects.get(username="jane")
    consent = user.consents.first()
    session = ConsentSession.objects.filter(user=user).order_by("-last_updated").first()

    generate_consent_pdf(consent, f"utils/{user.username}_ConsentForm_UCIGREGoR.pdf")
    generate_transcript_pdf(session, f"utils/{user.username}_ConsentChatTranscript.pdf")

    print(f"PDFs generated for {user.username}")


if __name__ == "__main__":
    main()
