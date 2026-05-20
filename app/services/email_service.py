import logging
from html import escape

import resend
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailConfigurationError(Exception):
    pass


class EmailRateLimitError(Exception):
    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__("Too many email requests")


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _rate_limit(key_parts, max_requests, window_seconds):
    cache_key = "email-rate:" + ":".join(str(part or "unknown") for part in key_parts)
    timestamps = cache.get(cache_key, [])
    now_ts = int(timezone.now().timestamp())

    timestamps = [ts for ts in timestamps if now_ts - ts < window_seconds]
    if len(timestamps) >= max_requests:
        retry_after = window_seconds - (now_ts - timestamps[0])
        raise EmailRateLimitError(max(retry_after, 1))

    timestamps.append(now_ts)
    cache.set(cache_key, timestamps, window_seconds)


def send_contact_email(request, form_data):
    user_name = form_data["name"].strip()
    user_email = form_data["email"].strip()
    user_phone = form_data.get("phone", "").strip()
    user_telegram = form_data.get("telegram_username", "").strip()
    user_message = form_data["message"].strip()

    _rate_limit(
        ("contact", user_email.lower(), _client_ip(request)),
        settings.CONTACT_EMAIL_RATE_LIMIT,
        settings.CONTACT_EMAIL_RATE_WINDOW_SECONDS,
    )

    if not settings.CONTACT_EMAIL_HOST_PASSWORD:
        raise EmailConfigurationError("CONTACT_EMAIL_HOST_PASSWORD is not configured")

    connection = get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=settings.CONTACT_EMAIL_HOST,
        port=settings.CONTACT_EMAIL_PORT,
        username=settings.CONTACT_EMAIL_HOST_USER,
        password=settings.CONTACT_EMAIL_HOST_PASSWORD,
        use_tls=settings.CONTACT_EMAIL_USE_TLS,
        use_ssl=settings.CONTACT_EMAIL_USE_SSL,
        fail_silently=False,
    )

    subject = f"Nabbiuwny Contact: {user_name}"
    text_body = (
        f"Name: {user_name}\n"
        f"Email: {user_email}\n"
        f"Phone: {user_phone or 'Not provided'}\n"
        f"Telegram: {user_telegram or 'Not provided'}\n\n"
        f"{user_message}"
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #172033; line-height: 1.6;">
      <h2 style="margin: 0 0 16px;">New Nabbiuwny contact message</h2>
      <p><strong>Name:</strong> {escape(user_name)}</p>
      <p><strong>Email:</strong> {escape(user_email)}</p>
      <p><strong>Phone:</strong> {escape(user_phone) if user_phone else "Not provided"}</p>
      <p><strong>Telegram:</strong> {escape(user_telegram) if user_telegram else "Not provided"}</p>
      <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
      <p style="white-space: pre-line;">{escape(user_message)}</p>
    </div>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.CONTACT_EMAIL_FROM,
        to=[settings.CONTACT_EMAIL_TO],
        reply_to=[user_email],
        connection=connection,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()

    logger.info("Contact email sent", extra={"reply_to": user_email})


def send_otp_email(email, otp, purpose="verification"):
    if not settings.RESEND_API_KEY:
        raise EmailConfigurationError("RESEND_API_KEY is not configured")

    resend.api_key = settings.RESEND_API_KEY

    subject = "Your Nabbiuwny verification code"
    intro = "Use this code to verify your email address."
    if purpose == "reset":
        subject = "Your Nabbiuwny password reset code"
        intro = "Use this code to reset your password."

    html = f"""
    <div style="margin:0;padding:24px;background:#f6f7fb;font-family:Arial,sans-serif;color:#172033;">
      <div style="max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
        <div style="padding:24px 28px;background:#0f6f64;color:#ffffff;">
          <h1 style="margin:0;font-size:22px;line-height:1.3;">Nabbiuwny</h1>
        </div>
        <div style="padding:28px;">
          <p style="margin:0 0 18px;font-size:16px;">{intro}</p>
          <div style="font-size:32px;letter-spacing:6px;font-weight:700;text-align:center;padding:18px 12px;margin:20px 0;background:#f3faf8;border-radius:8px;color:#0f6f64;">
            {otp}
          </div>
          <p style="margin:0;color:#556070;font-size:14px;">This code expires in {settings.OTP_EXPIRATION_MINUTES} minutes. If you did not request it, you can ignore this email.</p>
        </div>
      </div>
    </div>
    """
    text = (
        f"{intro}\n\n"
        f"Your Nabbiuwny code is: {otp}\n\n"
        f"This code expires in {settings.OTP_EXPIRATION_MINUTES} minutes."
    )

    resend.Emails.send(
        {
            "from": settings.TRANSACTIONAL_FROM_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html,
            "text": text,
        }
    )

    logger.info("OTP email sent", extra={"purpose": purpose})
