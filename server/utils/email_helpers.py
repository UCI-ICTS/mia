#!/usr/bin/env python
# utils/email_helpers.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, to_email, template_name, context, text_content=None, attachments=None):
    """
    Sends a multipart HTML email using a Django template, with optional attachments.

    Args:
        subject (str): Email subject.
        to_email (str or list): Recipient(s).
        template_name (str): Path to the HTML template.
        context (dict): Template context.
        text_content (str, optional): Fallback plain text content.
        attachments (list of tuples, optional): Each tuple = (filename, content, mimetype)
    """
    html_content = render_to_string(template_name, context)

    if text_content is None:
        text_content = context.get("reset_link") or context.get("activation_url") or "See email for details."

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [to_email] if isinstance(to_email, str) else to_email,
    )
    msg.attach_alternative(html_content, "text/html")

    if attachments:
        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)

    msg.send()


