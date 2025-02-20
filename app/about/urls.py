from django.urls import path


app_name='about'
from .views import about_us, home, send_email

urlpatterns = [
    path('',home,name='home'),
    path('about-us/', about_us, name='about_us'),
    path('send-email/', send_email, name='send_email'),
    
    # path('terms-and-conditions/', policy_detail, {'policy_type': 'terms'}, name='terms_and_conditions'),
    # path('refund-policy/', policy_detail, {'policy_type': 'refund'}, name='refund_policy'),
    # path('privacy-policy/', policy_detail, {'policy_type': 'privacy'}, name='privacy_policy'),
    # path('exchange-policy/', policy_detail, {'policy_type': 'exchange'}, name='exchange_policy'),
    
]




