
from urllib.parse import urlsplit, urlunsplit

from django import template
from django.template.defaultfilters import stringfilter

from project.phone_utils import phone_digits_for_url

register = template.Library()

INTERNAL_DOMAINS = {"nabbiuwny.com", "www.nabbiuwny.com"}

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    return float(value) / float(arg)



@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    return float(value) / float(arg)

@register.filter
@stringfilter
def split(value, separator):
    return value.split(separator)

@register.filter
@stringfilter
def trim(value):
    return value.strip()

@register.filter
def local_internal_url(value):
    if not value:
        return value

    raw_url = str(value).strip()
    parsed = urlsplit(raw_url)

    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() in INTERNAL_DOMAINS:
        path = parsed.path or "/"
        return urlunsplit(("", "", path, parsed.query, parsed.fragment))

    return raw_url

@register.filter
def whatsapp_phone(value):
    return phone_digits_for_url(value)

@register.simple_tag(takes_context=True)
def is_loved_by(context, course):
    request = context['request']
    return course.lovecourse_set.filter(student=request.user).exists()
