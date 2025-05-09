import django
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from django.conf import settings
import debug_toolbar
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('accounts/', include('accounts.urls',namespace='accounts')),
    path('a_d_m_i_n/', admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),

    path('favicon.ico/', RedirectView.as_view(url=staticfiles_storage.url('imgs/logo.ico'))),
    path('', include('about.urls',namespace='about')),
    # path('appointments/', include('appointments.urls',namespace='appointments')),
    # path('carts/', include('carts.urls',namespace='carts')),
    path('courses/', include('courses.urls',namespace='courses')),
    # path('payments/', include('payments.urls',namespace='payments')),
    # path('exams/', include('exams.urls',namespace='exams')),
    # path('loves/', include('loves.urls',namespace='loves')),
    path('subscriptions/', include('subscriptions.urls',namespace='subscriptions')),
    path('library/', include('library.urls',namespace='library')),
    path('assignment/', include('assignment.urls',namespace='assignment')),
    # path('freemeet/', include('freemeet.urls',namespace='freemeet')),
    path('chat/', include('chat.urls', namespace='chat')),
]
urlpatterns+=static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
)