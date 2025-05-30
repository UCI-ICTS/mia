#!/usr/bin/env python
# utils/api.py

# Swagger usage tip:
# In @swagger_auto_schema(responses={200: "Response Format"}),
# you can link to an OpenAPI-compatible schema or example object to reflect this shape.

from rest_framework.response import Response
from rest_framework import status as http_status
from typing import Optional, List, Dict, Any
from drf_yasg import openapi

ConsentResponseSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["status", "chat", "render", "session", "error"],
    properties={
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=["ok", "error"],
            description="Indicates success or failure of the request."
        ),
        "consent": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="The Consent Object."
        ),
        "chat": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="List of structured chat turns.",
            items=openapi.Items(type=openapi.TYPE_OBJECT)
        ),
        "render": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="UI element to render next (e.g., form or buttons).",
            additional_properties=True
        ),
        "session": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Optional metadata about the consent session.",
            additional_properties=True
        ),
        "error": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Error message if status is 'error'. Null otherwise.",
            nullable=True
        ),
    }
)


def consent_response_constructor(
    *,
    status_code: int,
    status_label: str = "ok",
    consent: Optional[Dict[str, Any]] = None,
    chat: Optional[List[Dict[str, Any]]] = None,
    render: Optional[Dict[str, Any]] = None,
    session: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Response:
    """
    Standardized response constructor for all consent chat responses.

    Args:
        status_code (int): HTTP status code, preferably from rest_framework.status
        status_label (str): Either 'ok' or 'error'.
        chat (list): List of chat turn dictionaries.
        render (dict): Render metadata for form/button prompts.
        session (dict): Optional session metadata.
        error (str): Optional error message.

    Returns:
        Response: DRF Response object with unified structure.
    """
    return Response({
        "status": status_label,
        "consent": consent,
        "chat": chat or [],
        "render": render,
        "session": session,
        "error": error,
    }, status=status_code)
