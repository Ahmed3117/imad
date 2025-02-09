from django.urls import path
from .views import payment_view, payment_callback
app_name='payments'
urlpatterns = [
    path('pay/<str:order_id>/', payment_view, name='pay'),
    path("callback/", payment_callback, name="payment_callback"),
]
