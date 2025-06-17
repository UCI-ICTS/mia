#!/usr/bin/env python
# utils/consent_form_writer.py

from datetime import datetime
import os
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model
from consentbot.models import Consent

User = get_user_model()

def generate_consent_pdf(consent, output_pdf_path):
    user = consent.user

    data_dict = {
        "record_id": str(consent.user_consent_id),
        "study_id":  "PMGRC",
        "pmgrc_id":  user.username,
        "date_of_birth": user.date_joined.strftime("%m/%d/%Y"),
        "participant_first_name": user.first_name,
        "participant_last_name": user.last_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "signature": consent.user_full_name_consent,
        "representative": "", 
        "datetime_now": datetime.now().strftime("%m/%d/%Y"),
        "store_sample_other_studies": consent.store_sample_other_studies,
        "store_phi_other_studies": consent.store_phi_other_studies,
        "return_primary_results": consent.return_primary_results,
        "return_actionable_secondary_results": consent.return_actionable_secondary_results,
        "return_secondary_results": consent.return_secondary_results,
        "statement": consent.consent_statements
    }

    # Render HTML template with data
    html_content = render_to_string("consent_form.html", data_dict)

    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(output_pdf_path)
    


def main():
    user = User.objects.get(username="jane")
    output_pdf_path = f"utils/{user.username}_ConsentForm_UCIGREGoR.pdf"
    # import pdb; pdb.set_trace()
    generate_consent_pdf(user.consents.first(), output_pdf_path)
    print(f"PDF generated: {output_pdf_path}")

if __name__ == "__main__":
    main()
