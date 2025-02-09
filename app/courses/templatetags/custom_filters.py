
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

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

@register.simple_tag(takes_context=True)
def is_loved_by(context, course):
    request = context['request']
    return course.lovecourse_set.filter(student=request.user).exists()