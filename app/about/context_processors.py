from admin_interface.models import Theme
from .models import CompanyInfo, CompanyInfoTranslation


def get_logo_url(request):
    theme = Theme.objects.filter(active=True).first()
    logo_url = theme.logo.url if theme and theme.logo else None

    return {
        'logo_url': logo_url
    }


def get_company_info(request):
    language = request.GET.get('lang', 'en')
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

    return {
        'company_info': company_info
    }

