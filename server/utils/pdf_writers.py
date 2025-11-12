#!/usr/bin/env python
# utils/pdf_writers.py

import os
import json
import urllib.request
from collections import defaultdict
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model
from consentbot.models import Consent, ConsentSession, ConsentScript, Document
from django.core.files import File
from pathlib import Path

User = get_user_model()

def generate_consent_pdf(consent, session):
    """
    Generate a filled PDF of the static consent form with participant responses.

    Args:
        consent (Consent): The Consent model instance.
        session (str): The Session  model instance.
    """
    
    file_name = f"{consent.user.username}_ConsentForm_UCIGREGoR.pdf"

    output_pdf_path = os.path.join(
        settings.MEDIA_ROOT,
        "pdfs",
        session.session_slug,
        file_name
    )

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
    
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    html_content = render_to_string("consent_form.html", data_dict)
    HTML(string=html_content).write_pdf(output_pdf_path)
    
    with open(output_pdf_path, "rb") as f:
        django_file = File(f)
        doc = Document(file_name=file_name,user=consent.user,session=session)
        # manually set relative path
        doc.file_path.name = f"pdfs/{session.session_slug}/{file_name}"
        doc.save()

def generate_transcript_pdf(session):
    """
    Generate a transcript-style PDF of the chat interaction during a consent session.

    Args:
        session (ConsentSession): The ConsentSession object.
    """

    file_name = f"{session.user.username}_ConsentChatTranscript.pdf"
    output_pdf_path = os.path.join(
        settings.MEDIA_ROOT,
        "pdfs",
        session.session_slug,
        file_name
    )
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    chat_turns = session.chat_turns.all().select_related("session", "user")
    parsed_turns = []

    for turn in chat_turns:
        node = turn.node
        image_path = None
        form_options = None
        render = node.get("render", {})
        render_type = render.get("type") if render else None
        render_media = render.get("content") if render else None

        # Image support
        if render_type == "image" and render_media:
            abs_path = os.path.join(settings.BASE_DIR, "static", "images", render_media)
            if os.path.exists(abs_path):
                image_path = f"file://{abs_path}"

        # Video support
        elif render_type == "video" and render_media:
            thumb_id = render_media.split("/")[-1].split("?")[0]
            thumb_name = f"{thumb_id}.png"
            abs_path = os.path.join(settings.BASE_DIR, "static", "images", thumb_name)
            if not os.path.exists(abs_path):
                urllib.request.urlretrieve(
                    f"https://img.youtube.com/vi/{thumb_id}/hqdefault.jpg", abs_path
                )
            image_path = f"file://{abs_path}"
            node["messages"].insert(0, f"Video link: {render_media}")

        # Form support
        elif render_type == "form":
            form_fields = json.dumps(render.get("fields", []), indent=2)
            form_options = {
                "form_id": render.get("form_id", "Null"),
                "description": render.get("description", " "),
                "fields": form_fields,
            }

        parsed_turns.append({
            "node": node,
            "node_id": node.get("node_id", ""),
            "speaker": node.get("type", "bot"),
            "messages": node.get("messages", []),
            "image_path": image_path,
            "form_options": form_options,
            "timestamp": turn.timestamp,
        })

    context = {
        "chat_turns": parsed_turns,
        "first_name": session.user.first_name,
        "last_name": session.user.last_name,
        "datetime_now": datetime.now().strftime("%m/%d/%Y"),
    }

    html_content = render_to_string("chat_transcript.html", context)
    HTML(string=html_content).write_pdf(output_pdf_path)

    with open(output_pdf_path, "rb") as f:
        django_file = File(f)
        doc = Document(file_name=file_name,user=session.user,session=session)
        # manually set relative path
        doc.file_path.name = f"pdfs/{session.session_slug}/{file_name}"
        doc.save()


def generate_full_graph_transcript_pdf():
    """
    Render a transcript PDF of the entire consent chat graph grouped by workflow.

    This function traverses the consent script graph, groups turns by workflow,
    and renders a PDF including text, metadata, and inline images.
    """

    graph = ConsentScript.objects.all()[0].script
    output_pdf_path = os.path.join(settings.MEDIA_ROOT, "pdfs", "ConsentTranscript.pdf")

    visited = set()
    grouped_turns_dict = defaultdict(list)
    workflow_labels = {}

    def walk(node_id):
        if node_id in visited:
            return
        visited.add(node_id)

        node = graph.get(node_id, {})
        workflow = node.get("metadata", {}).get("workflow", "") or "main"

        if workflow not in workflow_labels:
            workflow_labels[workflow] = workflow.replace("_", " ").title() or "General"

        image_path = None
        form_options = None
        render_media = node.get("render", {}).get("content")
        
        if node.get("render", {}).get("type") == "image" and render_media:
            absolute_path = os.path.join(settings.BASE_DIR, "static", "images", render_media)
            if os.path.exists(absolute_path):
                image_path = f"file://{absolute_path}"
        
        elif node.get("render", {}).get("type") == "video" and render_media:
            thumb = render_media.split('/')[-1]
            node['messages'].insert(0, f"Video link: {render_media}")
            absolute_path = os.path.join(settings.BASE_DIR, "static", "images", f"{thumb}.png")
            if not os.path.exists(absolute_path):
                urllib.request.urlretrieve(f"https://img.youtube.com/vi/{thumb}/hqdefault.jpg", filename=absolute_path)
            image_path = absolute_path

        elif node.get("render", {}).get("type") == "form":
            form = node.get("render", {})
            pretty_json = json.dumps(form.get("fields", []), indent=2)
            form_options = {
                "form_id": form.get("form_id", "Null"),
                "description": form.get("description", " "),
                "fields": pretty_json,
            }
            
        grouped_turns_dict[workflow].append({
            "node": node,
            "node_id": node_id,
            "speaker": node.get("type", "bot"),
            "messages": node.get("messages", []),
            "image_path": image_path,
            "form_options": form_options,
            "parent_ids": node.get("parent_ids", []),
            "child_ids": node.get("child_ids", [])
        })

        for child_id in node.get("child_ids", []):
            walk(child_id)

    start_node_id = next((nid for nid, node in graph.items() if node.get("type") == "start"), None)
    if not start_node_id:
        raise ValueError("No start node found in the graph.")

    for first_id in graph[start_node_id].get("child_ids", []):
        walk(first_id)

    context = {
        "workflow_sections": [
            {
                "label": workflow_labels.get(workflow, workflow),
                "turns": turns
            }
            for workflow, turns in grouped_turns_dict.items()
        ],
        "first_name": "User",
        "last_name": "Transcript",
        "datetime_now": datetime.now().strftime("%m/%d/%Y %I:%M %p"),
    }

    html_content = render_to_string("full_chat_output.html", context)

    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    HTML(string=html_content, base_url=settings.STATIC_ROOT).write_pdf(output_pdf_path)
    
    return output_pdf_path

def main():
    user = User.objects.get(username="jane")
    consent = user.consents.first()
    session = ConsentSession.objects.filter(user=user).order_by("-last_updated").first()

    generate_consent_pdf(consent, f"utils/{user.username}_ConsentForm_UCIGREGoR.pdf")
    generate_transcript_pdf(session)

    print(f"PDFs generated for {user.username}")


if __name__ == "__main__":
    main()
