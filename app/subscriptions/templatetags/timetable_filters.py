from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def model_translations(obj):
    """
    Get translation data for a model object as JSON
    Returns a data attribute with translations for use in JavaScript
    """
    translations = {}
    
    if hasattr(obj, 'translations'):
        for trans in obj.translations.all():
            translations[trans.language] = trans.translated_name
    
    if translations:
        return json.dumps(translations)
    return '{}'


@register.filter
def translated_name(obj, language='en'):
    """
    Get translated name for an object
    """
    if hasattr(obj, 'get_translated_name'):
        return obj.get_translated_name(language)
    return str(obj)
