from admin_interface.models import Theme



def get_logo_url(request):
    theme = Theme.objects.filter(active=True).first() 
    logo_url = theme.logo.url if theme and theme.logo else None
        
    return {
        'logo_url': logo_url
    }

