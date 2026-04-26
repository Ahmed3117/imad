from django.urls import path

app_name = "about"
from .views import about_us, book_free_session, home, send_email

urlpatterns = [
    path("", home, name="home"),
    path("about-us/", about_us, name="about_us"),
    path("send-email/", send_email, name="send_email"),
    path("book-free-session/", book_free_session, name="book_free_session"),
]
