import secrets

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from .email_service import EmailRateLimitError, send_otp_email


SESSION_KEY_TEMPLATE = "{purpose}_otp_verification"


def _normalize_email(email):
    return (email or "").strip().lower()


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _hash_otp(email, otp, purpose):
    return salted_hmac(
        f"accounts.otp.{purpose}",
        f"{_normalize_email(email)}:{otp}",
        secret=settings.SECRET_KEY,
    ).hexdigest()


def _rate_limit(request, email, purpose):
    now_ts = int(timezone.now().timestamp())
    window = settings.OTP_RATE_LIMIT_WINDOW_SECONDS
    cache_key = (
        f"otp-rate:{purpose}:"
        f"{_normalize_email(email)}:{_client_ip(request) or 'unknown'}"
    )
    timestamps = cache.get(cache_key, [])
    timestamps = [ts for ts in timestamps if now_ts - ts < window]

    if len(timestamps) >= settings.OTP_RATE_LIMIT_MAX_REQUESTS:
        retry_after = window - (now_ts - timestamps[0])
        raise EmailRateLimitError(max(retry_after, 1))

    timestamps.append(now_ts)
    cache.set(cache_key, timestamps, window)


def generate_otp():
    upper_bound = 10**settings.OTP_LENGTH
    lower_bound = 10 ** (settings.OTP_LENGTH - 1)
    return str(secrets.randbelow(upper_bound - lower_bound) + lower_bound)


def create_and_send_otp(request, email, purpose="verification"):
    email = _normalize_email(email)
    _rate_limit(request, email, purpose)

    otp = generate_otp()
    expires_at = timezone.now() + timezone.timedelta(
        minutes=settings.OTP_EXPIRATION_MINUTES
    )
    session_key = SESSION_KEY_TEMPLATE.format(purpose=purpose)

    request.session[session_key] = {
        "email": email,
        "otp_hash": _hash_otp(email, otp, purpose),
        "expires_at": expires_at.isoformat(),
    }
    request.session.modified = True

    send_otp_email(email, otp, purpose=purpose)


def verify_otp(request, email, otp, purpose="verification", invalidate=True):
    session_key = SESSION_KEY_TEMPLATE.format(purpose=purpose)
    stored = request.session.get(session_key)
    email = _normalize_email(email)
    otp = (otp or "").strip()

    if not stored:
        return False, "Session expired"

    expires_at = timezone.datetime.fromisoformat(stored["expires_at"])
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())

    if timezone.now() > expires_at:
        invalidate_otp(request, purpose)
        return False, "OTP expired"

    if stored.get("email") != email:
        return False, "Invalid OTP"

    expected_hash = stored.get("otp_hash", "")
    submitted_hash = _hash_otp(email, otp, purpose)
    if not constant_time_compare(expected_hash, submitted_hash):
        return False, "Invalid OTP"

    if invalidate:
        invalidate_otp(request, purpose)

    return True, None


def otp_session_is_valid(request, email, purpose="verification"):
    session_key = SESSION_KEY_TEMPLATE.format(purpose=purpose)
    stored = request.session.get(session_key)
    email = _normalize_email(email)

    if not stored or stored.get("email") != email:
        return False

    expires_at = timezone.datetime.fromisoformat(stored["expires_at"])
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())

    if timezone.now() > expires_at:
        invalidate_otp(request, purpose)
        return False

    return True


def invalidate_otp(request, purpose="verification"):
    session_key = SESSION_KEY_TEMPLATE.format(purpose=purpose)
    if session_key in request.session:
        del request.session[session_key]
        request.session.modified = True
