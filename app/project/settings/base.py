from pathlib import Path
import os
import dotenv

# ─────────────────────────────────────────────
# Base directory & environment
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file (works for both local and production; in prod the real values
# are injected via Docker / system env, so dotenv simply won't override them)
dotenv.load_dotenv(BASE_DIR / '.env')

# ─────────────────────────────────────────────
# Security – overridden per environment
# ─────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-+a&_h)1p4ert$nm!%@8t$ie^qku11#$+qqk&5$v%$-ft4tv%g*')

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'local')

# ─────────────────────────────────────────────
# Application definition
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'about.apps.AboutConfig',
    'courses.apps.CoursesConfig',
    'subscriptions',
    'library',
    'assignment',
    "crispy_forms",
    "crispy_bootstrap5",
    'rest_framework',
    'ckeditor',
    'channels',
    'chat',
]

ASGI_APPLICATION = 'project.asgi.application'
WSGI_APPLICATION = 'project.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'courses.middleware.RequestMiddleware',
    'courses.middleware.LocationMiddleware',
]

ROOT_URLCONF = 'project.urls'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

INTERNAL_IPS = [
    "127.0.0.1",
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'about.context_processors.get_logo_url',
                'about.context_processors.get_company_info',
                # Injects META_PIXEL_ID and META_DOMAIN_VERIFICATION into every template
                'about.context_processors.get_meta_pixel_id',
            ],
        },
    },
]

# ─────────────────────────────────────────────
# Database – values come from environment
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'django_db'),
        'USER': os.getenv('DB_USER', 'django_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'django_password'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}

# ─────────────────────────────────────────────
# Password validation
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', 'English'),
    ('ar', 'Arabic'),
]
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ─────────────────────────────────────────────
# Static & media files
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# Crispy Forms
# ─────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ─────────────────────────────────────────────
# Email
# Contact form uses Namecheap SMTP. OTP / auth emails use Resend API.
# ─────────────────────────────────────────────
CONTACT_EMAIL_HOST = os.environ.get('CONTACT_EMAIL_HOST', 'mail.privateemail.com')
CONTACT_EMAIL_PORT = int(os.environ.get('CONTACT_EMAIL_PORT', '587'))
CONTACT_EMAIL_USE_TLS = os.environ.get('CONTACT_EMAIL_USE_TLS', 'True') == 'True'
CONTACT_EMAIL_USE_SSL = os.environ.get('CONTACT_EMAIL_USE_SSL', 'False') == 'True'
CONTACT_EMAIL_HOST_USER = os.environ.get('CONTACT_EMAIL_HOST_USER', 'contact@nabbiuwny.com')
CONTACT_EMAIL_HOST_PASSWORD = os.environ.get('CONTACT_EMAIL_HOST_PASSWORD', 'Bluebook@2026')
CONTACT_EMAIL_FROM = os.environ.get('CONTACT_EMAIL_FROM', 'contact@nabbiuwny.com')
CONTACT_EMAIL_TO = os.environ.get('CONTACT_EMAIL_TO', 'contact@nabbiuwny.com')
CONTACT_EMAIL_RATE_LIMIT = int(os.environ.get('CONTACT_EMAIL_RATE_LIMIT', '5'))
CONTACT_EMAIL_RATE_WINDOW_SECONDS = int(os.environ.get('CONTACT_EMAIL_RATE_WINDOW_SECONDS', '600'))

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
TRANSACTIONAL_FROM_EMAIL = os.environ.get(
    'TRANSACTIONAL_FROM_EMAIL',
    'Nabbiuwny <noreply@nabbiuwny.com>',
)
DEFAULT_FROM_EMAIL = TRANSACTIONAL_FROM_EMAIL

OTP_LENGTH = int(os.environ.get('OTP_LENGTH', '6'))
OTP_EXPIRATION_MINUTES = int(os.environ.get('OTP_EXPIRATION_MINUTES', '5'))
OTP_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get('OTP_RATE_LIMIT_MAX_REQUESTS', '3'))
OTP_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('OTP_RATE_LIMIT_WINDOW_SECONDS', '300'))

# ─────────────────────────────────────────────
# Zoom API
# ─────────────────────────────────────────────
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', '')
CLIENT_ID = os.environ.get('CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')

TOKEN_URL = "https://zoom.us/oauth/token"
MEETING_URL = "https://api.zoom.us/v2/users/me/meetings"
# Overridden in local.py for local dev
BASE_URL = os.environ.get('BASE_URL', 'https://nabbiuwny.com')

# ─────────────────────────────────────────────
# Meta / Facebook Integration
# ─────────────────────────────────────────────
META_PIXEL_ID = os.environ.get('META_PIXEL_ID', '1339327481347453')
META_DOMAIN_VERIFICATION = os.environ.get('META_DOMAIN_VERIFICATION', 'd6g2chn9l27eimvptlbwamey5yj3ju')
META_CAPI_ACCESS_TOKEN = os.environ.get('META_CAPI_ACCESS_TOKEN', 'EAAUeTTiaNvoBRXKxzUvyZBgWLHe8HVsqDNXJdW7jCWkzGklG9TZAfGKAffiS9NCUxwcZC0W0JYRLpGoPLUg1i3vnNV6merZAY6HyIOVEoumAcLlvR2adKuomMBHZC26pCiMldux3fcweTzoMp6Jork0vgFMFWQFQCQyCYKJNUM1p8V1Blbp5oUz0AOxSbem7ENgZDZD')

# ─────────────────────────────────────────────
# Django Admin ordering
# ─────────────────────────────────────────────
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

ADMIN_ORDERING = (
    ('about', (
        'CompanyInfo',
        'HomePageContent', 'HomePageFeature', 'HomePageVideoPoint',
        'FreeSession',
    )),
    ('accounts', (
        'User', 'StudentProfile',
        'TeacherInfo',
        'TeacheroomAccount', 'ZoomAccount',
    )),
    ('courses', (
        'Level',
        'Track',
        'Course',
    )),
    ('library', (
        'LibraryCategory', 'CourseLibrary', 'MyLibrary',
    )),
    ('subscriptions', (
        'StudyGroup', 'GroupTime', 'JoinRequest',
        'Lecture', 'LectureFile', 'LectureNote', 'LectureVisitHistory',
        'StudyGroupResource', 'StudyGroupReport',
    )),
    ('assignment', (
        'Assignment', 'StudentAnswer',
    )),
    ('chat', (
        'Room', 'Message',
    )),
    ('auth', ('Group',)),
    ('admin_interface', ('Theme',)),
)


def get_app_list(self, request, app_label=None):
    """Reorder the appearance of apps and models in the Django admin."""
    app_dict = self._build_app_dict(request, app_label)
    if not app_dict:
        return

    NEW_ADMIN_ORDERING = []
    if app_label:
        for ao in ADMIN_ORDERING:
            if ao[0] == app_label:
                NEW_ADMIN_ORDERING.append(ao)
                break

    if not app_label:
        for app_key in list(app_dict.keys()):
            if not any(app_key in ao_app for ao_app in ADMIN_ORDERING):
                app_dict.pop(app_key)

    app_list = sorted(
        app_dict.values(),
        key=lambda x: [ao[0] for ao in ADMIN_ORDERING].index(x['app_label'])
    )

    for app, ao in zip(app_list, NEW_ADMIN_ORDERING or ADMIN_ORDERING):
        if app['app_label'] == ao[0]:
            for model in list(app['models']):
                if model['object_name'] not in ao[1]:
                    app['models'].remove(model)
            app['models'].sort(key=lambda x: ao[1].index(x['object_name']))

    return app_list


# Override the default get_app_list method
admin.AdminSite.get_app_list = get_app_list
