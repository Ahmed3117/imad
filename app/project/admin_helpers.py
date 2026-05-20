import re

from django.utils.text import capfirst
from django.utils.html import format_html, format_html_join

from project.phone_utils import phone_digits_for_url


CONTACT_ICON_BASE_STYLE = (
    "display:inline-flex;align-items:center;justify-content:center;"
    "width:24px;height:24px;border-radius:50%;font-size:11px;"
    "font-weight:700;line-height:1;text-decoration:none;margin-inline-end:4px;"
)


def normalize_telegram_username(username):
    if not username:
        return ""

    cleaned = str(username).strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if cleaned.startswith(prefix):
            cleaned = cleaned.removeprefix(prefix)
            break

    cleaned = cleaned.lstrip("@").strip()
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", cleaned):
        return cleaned
    return ""


def contact_link_icons(phone=None, email=None, telegram_username=None):
    links = []

    whatsapp_phone = phone_digits_for_url(phone)
    if whatsapp_phone:
        links.append(
            format_html(
                '<a href="https://wa.me/{}" target="_blank" rel="noopener noreferrer" '
                'title="WhatsApp" aria-label="WhatsApp" style="{}background:#25d366;color:#fff;">W</a>',
                whatsapp_phone,
                CONTACT_ICON_BASE_STYLE,
            )
        )

    telegram = normalize_telegram_username(telegram_username)
    if telegram:
        links.append(
            format_html(
                '<a href="https://t.me/{}" target="_blank" rel="noopener noreferrer" '
                'title="Telegram" aria-label="Telegram" style="{}background:#229ed9;color:#fff;">T</a>',
                telegram,
                CONTACT_ICON_BASE_STYLE,
            )
        )
    elif whatsapp_phone:
        links.append(
            format_html(
                '<a href="https://t.me/+{}" target="_blank" rel="noopener noreferrer" '
                'title="Telegram by phone" aria-label="Telegram by phone" '
                'style="{}background:#229ed9;color:#fff;">T</a>',
                whatsapp_phone,
                CONTACT_ICON_BASE_STYLE,
            )
        )

    if email:
        links.append(
            format_html(
                '<a href="mailto:{}" title="Email" aria-label="Email" '
                'style="{}background:#4b5563;color:#fff;">@</a>',
                email,
                CONTACT_ICON_BASE_STYLE,
            )
        )

    if not links:
        return "-"

    return format_html_join("", "{}", ((link,) for link in links))


class UnhandledChangelistMixin:
    handled_field = "handled"
    unhandled_label = "unhandled"

    def get_unhandled_count(self, request):
        return self.get_queryset(request).filter(**{self.handled_field: False}).count()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        unhandled_count = self.get_unhandled_count(request)
        extra_context["unhandled_count"] = unhandled_count
        extra_context["title"] = (
            f"{capfirst(self.model._meta.verbose_name_plural)} "
            f"({unhandled_count} {self.unhandled_label})"
        )
        return super().changelist_view(request, extra_context=extra_context)
