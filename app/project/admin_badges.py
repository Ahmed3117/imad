from django.templatetags.static import static


def get_dynamic_logo_url():
    from about.models import CompanyInfo
    company = CompanyInfo.objects.last()
    if company and company.logo:
        return company.logo.url
    return static("imgs/hero/logo.png")


def unhandled_freesession_count(request):
    from about.models import FreeSession
    return FreeSession.objects.filter(handled=False).count()


def unhandled_contact_count(request):
    from about.models import ContactMessage
    return ContactMessage.objects.filter(handled=False).count()


def unhandled_joinrequest_count(request):
    from subscriptions.models import JoinRequest
    return JoinRequest.objects.filter(handled=False).count()
