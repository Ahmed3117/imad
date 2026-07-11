from django.urls import path

app_name = "about"
from .views import (
    about_us,
    book_free_session,
    cookie_policy,
    home,
    family_bundle_page,
    payment_terms,
    privacy_policy,
    refund_policy,
    send_email,
    terms_conditions,
)

urlpatterns = [
    path("", home, name="home"),
    path("family-bundle/", family_bundle_page, name="family_bundle_page"),
    path("about-us/", about_us, name="about_us"),
    path("send-email/", send_email, name="send_email"),
    path("book-free-session/", book_free_session, name="book_free_session"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
    path("terms-conditions/", terms_conditions, name="terms_conditions"),
    path("refund-policy/", refund_policy, name="refund_policy"),
    path("cookie-policy/", cookie_policy, name="cookie_policy"),
    path("payment-terms/", payment_terms, name="payment_terms"),
]
