import os
from django.conf import settings
from .models import CompanyInfo, CompanyInfoTranslation


def get_meta_pixel_id(request):
    return {
        'META_PIXEL_ID': getattr(settings, 'META_PIXEL_ID', '') or os.environ.get('META_PIXEL_ID', ''),
        'META_DOMAIN_VERIFICATION': getattr(settings, 'META_DOMAIN_VERIFICATION', '') or os.environ.get(
            'META_DOMAIN_VERIFICATION',
            os.environ.get('FACEBOOK_DOMAIN_VERIFICATION', '')
        ),
    }


def get_logo_url(request):
    company = CompanyInfo.objects.last()
    url = None
    if company and company.logo:
        url = company.logo.url
    return {
        'logo_url': url
    }


def get_company_info(request):
    language = request.GET.get('lang')
    if not language:
        language = request.COOKIES.get('django_language') or 'en'
    company_info = CompanyInfo.objects.last()

    if not company_info:
        return {'company_info': None}

    translation = CompanyInfoTranslation.objects.filter(
        company_info=company_info,
        language=language
    ).first()

    if translation:
        company_info.name = translation.translated_name or company_info.name
        company_info.description = translation.translated_description or company_info.description

    company_info.email = getattr(settings, 'CONTACT_EMAIL_TO', company_info.email)

    return {
        'company_info': company_info
    }


