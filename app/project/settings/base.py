from pathlib import Path
import os
import dotenv
from django.templatetags.static import static
from django.urls import reverse_lazy

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
    'unfold',
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

# ────────────────────────────────────────────
# Meta / Facebook Integration
# ─────────────────────────────────────────────
META_PIXEL_ID = os.environ.get('META_PIXEL_ID', '1339327481347453')
META_DOMAIN_VERIFICATION = os.environ.get('META_DOMAIN_VERIFICATION', 'd6g2chn9l27eimvptlbwamey5yj3ju')
META_CAPI_ACCESS_TOKEN = os.environ.get('META_CAPI_ACCESS_TOKEN', 'EAAUeTTiaNvoBRXKxzUvyZBgWLHe8HVsqDNXJdW7jCWkzGklG9TZAfGKAffiS9NCUxwcZC0W0JYRLpGoPLUg1i3vnNV6merZAY6HyIOVEoumAcLlvR2adKuomMBHZC26pCiMldux3fcweTzoMp6Jork0vgFMFWQFQCQyCYKJNUM1p8V1Blbp5oUz0AOxSbem7ENgZDZD')

# ─────────────────────────────────────────────
# Django Admin sidebar
# ─────────────────────────────────────────────
# UNFOLD Admin Configuration
# ─────────────────────────────────────────────
UNFOLD = {
    "SITE_TITLE": "Nabbiuwny Admin",
    "SITE_HEADER": "Nabbiuwny",
    "SITE_LOGO": {
        "light": lambda request: static("imgs/hero/logo.png"),
        "dark": lambda request: static("imgs/hero/logo.png"),
    },
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "Requests",
                "collapsible": True,
                "items": [
                    {
                        "title": "Free Session Requests",
                        "icon": "mail",
                        "link": reverse_lazy("admin:about_freesession_changelist"),
                    },
                    {
                        "title": "Contact Messages",
                        "icon": "chat",
                        "link": reverse_lazy("admin:about_contactmessage_changelist"),
                    },
                    {
                        "title": "Join Requests",
                        "icon": "person_add",
                        "link": reverse_lazy("admin:subscriptions_joinrequest_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Accounts",
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Zoom Accounts",
                        "icon": "videocam",
                        "link": reverse_lazy("admin:accounts_zoomaccount_changelist"),
                    },
                    {
                        "title": "Account Deletion Requests",
                        "icon": "delete_forever",
                        "link": reverse_lazy("admin:about_accountdeletionrequest_changelist"),
                    },
                ],
            },
            {
                "title": "Courses",
                "collapsible": True,
                "items": [
                    {
                        "title": "Levels",
                        "icon": "signal_cellular_alt",
                        "link": reverse_lazy("admin:courses_level_changelist"),
                    },
                    {
                        "title": "Tracks",
                        "icon": "route",
                        "link": reverse_lazy("admin:courses_track_changelist"),
                    },
                    {
                        "title": "Courses",
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:courses_course_changelist"),
                    },
                ],
            },
            {
                "title": "Study Groups",
                "collapsible": True,
                "items": [
                    {
                        "title": "Study Groups",
                        "icon": "groups",
                        "link": reverse_lazy("admin:subscriptions_studygroup_changelist"),
                    },
                ],
            },
            {
                "title": "Library",
                "collapsible": True,
                "items": [
                    {
                        "title": "Library Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:library_librarycategory_changelist"),
                    },
                    {
                        "title": "Course Libraries",
                        "icon": "folder",
                        "link": reverse_lazy("admin:library_courselibrary_changelist"),
                    },
                ],
            },
            {
                "title": "Home Page",
                "collapsible": True,
                "items": [
                    {
                        "title": "Company Info",
                        "icon": "business",
                        "link": reverse_lazy("admin:about_companyinfo_changelist"),
                    },
                    {
                        "title": "Home Page Content",
                        "icon": "home",
                        "link": reverse_lazy("admin:about_homepagecontent_changelist"),
                    },
                    {
                        "title": "Legal Pages",
                        "icon": "gavel",
                        "link": reverse_lazy("admin:about_legalpage_changelist"),
                    },
                ],
            },
            {
                "title": "System",
                "collapsible": True,
                "items": [
                    {
                        "title": "Groups",
                        "icon": "settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}


# ─────────────────────────────────────────────
# Legacy sidebar reference (kept for documentation; UNFOLD SIDEBAR above is active)
# ─────────────────────────────────────────────
ADMIN_SIDEBAR_GROUPS = [
    {
        'name': 'Requests',
        'slug': 'requests',
        'models': [
            'about.FreeSession',
            'about.ContactMessage',
            'subscriptions.JoinRequest',
        ],
    },
    {
        'name': 'Users & Accounts',
        'slug': 'users_accounts',
        'models': [
            'accounts.User',
            'accounts.ZoomAccount',
            'about.AccountDeletionRequest',
        ],
    },
    {
        'name': 'Courses',
        'slug': 'courses',
        'models': [
            'courses.Level',
            'courses.Track',
            'courses.Course',
        ],
    },
    {
        'name': 'Study Groups',
        'slug': 'study_groups',
        'models': [
            'subscriptions.StudyGroup',
        ],
    },
    {
        'name': 'Library',
        'slug': 'library',
        'models': [
            'library.LibraryCategory',
            'library.CourseLibrary',
        ],
    },
    {
        'name': 'Home Page',
        'slug': 'home_page',
        'models': [
            'about.CompanyInfo',
            'about.HomePageContent',
            'about.LegalPage',
        ],
    },
    {
        'name': 'System',
        'slug': 'system',
        'models': [
            'auth.Group',
        ],
    },
]

ADMIN_VISIBLE_MODEL_KEYS = {
    model_key
    for group in ADMIN_SIDEBAR_GROUPS
    for model_key in group['models']
}

ADMIN_ORDERING = {}
for group in ADMIN_SIDEBAR_GROUPS:
    for model_key in group['models']:
        app_label, object_name = model_key.split('.', 1)
        ADMIN_ORDERING.setdefault(app_label, []).append(object_name)

ADMIN_ORDER_LIST = list(ADMIN_ORDERING.keys())

# Models that have a "handled" boolean field for badge counting
UNHANDLED_BADGE_MODELS = {
    'about.FreeSession': lambda: __import__('about.models', fromlist=['FreeSession']).FreeSession.objects.filter(handled=False).count(),
    'about.ContactMessage': lambda: __import__('about.models', fromlist=['ContactMessage']).ContactMessage.objects.filter(handled=False).count(),
    'subscriptions.JoinRequest': lambda: __import__('subscriptions.models', fromlist=['JoinRequest']).JoinRequest.objects.filter(handled=False).count(),
}


# Admin ordering configuration — the monkey-patch in about/apps.py is DISABLED
# because UNFOLD provides its own sidebar via the UNFOLD["SIDEBAR"] setting above.
