"""
Meta Conversions API (CAPI) — server-side event sender.

Usage:
    from about.meta_capi import send_lead_event, send_contact_event

    send_lead_event(request, email="user@example.com", phone="+1234567890")
    send_contact_event(request)

Docs: https://developers.facebook.com/docs/marketing-api/conversions-api
"""

import hashlib
import json
import logging
import os
import time
import uuid

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PIXEL_ID = getattr(settings, 'META_PIXEL_ID', '') or os.environ.get("META_PIXEL_ID", "")
ACCESS_TOKEN = getattr(settings, 'META_CAPI_ACCESS_TOKEN', '') or os.environ.get("META_CAPI_ACCESS_TOKEN", "")
CAPI_URL = "https://graph.facebook.com/v19.0/{pixel_id}/events"


def _sha256(value: str) -> str:
    """Return lowercase SHA-256 hash of a stripped string (Meta requirement)."""
    if not value:
        return ""
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def _get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _get_fbp(request) -> str:
    """Read _fbp cookie set by the browser Pixel."""
    return request.COOKIES.get("_fbp", "")


def _get_fbc(request) -> str:
    """Read _fbc cookie (set when user clicks a Facebook ad)."""
    return request.COOKIES.get("_fbc", "")


def _build_user_data(request, email: str = "", phone: str = "") -> dict:
    user_data = {
        "client_ip_address": _get_client_ip(request),
        "client_user_agent": request.META.get("HTTP_USER_AGENT", ""),
    }

    fbp = _get_fbp(request)
    if fbp:
        user_data["fbp"] = fbp

    fbc = _get_fbc(request)
    if fbc:
        user_data["fbc"] = fbc

    if email:
        user_data["em"] = [_sha256(email)]

    if phone:
        # Strip non-digits for hashing
        clean_phone = "".join(filter(str.isdigit, phone))
        if clean_phone:
            user_data["ph"] = [_sha256(clean_phone)]

    # If user is authenticated, add hashed email from account
    if request.user.is_authenticated:
        if not email and hasattr(request.user, "email") and request.user.email:
            user_data["em"] = [_sha256(request.user.email)]
        if not phone and hasattr(request.user, "phone") and request.user.phone:
            clean_phone = "".join(filter(str.isdigit, str(request.user.phone)))
            if clean_phone:
                user_data["ph"] = [_sha256(clean_phone)]

    return user_data


def send_event(
    request,
    event_name: str,
    event_id: str = "",
    email: str = "",
    phone: str = "",
    custom_data: dict = None,
) -> bool:
    """
    Send a single event to Meta Conversions API.

    Returns True on success, False on failure.
    """
    if not PIXEL_ID or not ACCESS_TOKEN:
        logger.debug(
            "Meta CAPI skipped: META_PIXEL_ID or META_CAPI_ACCESS_TOKEN not set."
        )
        return False

    if not event_id:
        event_id = str(uuid.uuid4())

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(time.time()),
                "event_id": event_id,
                "event_source_url": request.build_absolute_uri(),
                "action_source": "website",
                "user_data": _build_user_data(request, email=email, phone=phone),
            }
        ],
        # Set to "EVENT_TEST" + test_event_code while testing, remove in production
        # "test_event_code": "TEST12345",
    }

    if custom_data:
        payload["data"][0]["custom_data"] = custom_data

    url = CAPI_URL.format(pixel_id=PIXEL_ID)
    params = {"access_token": ACCESS_TOKEN}

    try:
        response = requests.post(url, params=params, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info("Meta CAPI event '%s' sent successfully.", event_name)
            return True
        else:
            logger.warning(
                "Meta CAPI event '%s' failed: %s %s",
                event_name,
                response.status_code,
                response.text,
            )
            return False
    except requests.RequestException as exc:
        logger.error("Meta CAPI request error for event '%s': %s", event_name, exc)
        return False


# ── Convenience helpers ────────────────────────────────────────────────────────

def send_lead_event(request, email: str = "", phone: str = "", event_id: str = "") -> bool:
    """
    Fire a 'Lead' server-side event — call this when a free session is booked.
    Pass the same event_id that was sent to fbq('track', 'Lead') on the browser
    to enable deduplication.
    """
    return send_event(
        request,
        event_name="Lead",
        event_id=event_id,
        email=email,
        phone=phone,
        custom_data={
            "content_name": "Free Session Booking",
            "content_category": "Free Trial",
        },
    )


def send_contact_event(request, email: str = "", event_id: str = "") -> bool:
    """
    Fire a 'Contact' server-side event — call this when the contact form is submitted.
    """
    return send_event(
        request,
        event_name="Contact",
        event_id=event_id,
        email=email,
    )


def send_page_view_event(request) -> bool:
    """
    Fire a 'PageView' server-side event.
    Useful for pages where the browser Pixel may be blocked.
    """
    return send_event(request, event_name="PageView")
