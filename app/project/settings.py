from pathlib import Path
import os
import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# GEOIP_PATH = os.path.join(BASE_DIR, 'geoip')
#SECRET_KEY =env('SECRET_KEY')
SECRET_KEY = "django-insecure-+a&_h)1p4ert$nm!%@8t$ie^qku11#$+qqk&5$v%$-ft4tv%g*"
DEBUG =True 

ALLOWED_HOSTS = ['*', "localhost", "50.19.183.215","https://2a1e-45-100-68-117.ngrok-free.app"]
# ALLOWED_HOSTS = ['*', "localhost", "50.19.183.215"]

CSRF_TRUSTED_ORIGINS = [
    # 'https://2a1e-45-100-68-117.ngrok-free.app',
    # Add any other ngrok URLs here if you're using multiple
]


# Load environment variables from .env file
dotenv.load_dotenv()


ACCOUNT_ID = os.environ.get('ACCOUNT_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

# Zoom API URLs
TOKEN_URL = "https://zoom.us/oauth/token"
MEETING_URL = "https://api.zoom.us/v2/users/me/meetings"
# BASE_URL = "https://nabbiuwny.com"
BASE_URL = "http://127.0.0.1:8800"

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

AUTH_USER_MODEL ='accounts.User'



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
    # ...
    "127.0.0.1",
    # ...
]



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'about.context_processors.get_logo_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

ASGI_APPLICATION = 'project.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}



LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('ar', 'Arabic'),
]

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.getenv('DB_NAME'),  # Default to 'bluebook' if not set
#         'USER': os.getenv('DB_USER'),      # Default to 'root' if not set
#         'PASSWORD': os.getenv('DB_PASSWORD'),  # Default to 'haitham' if not set
#         'HOST': os.getenv('DB_HOST'),     # Default to 'mysql' if not set
#         'PORT': os.getenv('DB_PORT'),      # Default to '3306' if not set
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

STATIC_URL  = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# Define STATIC_ROOT for collectstatic to gather files
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = "/media/"
#MEDIA_ROOT = BASE_DIR/"media"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Cairo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

#SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'hicode.academy.contact@gmail.com'
# EMAIL_HOST_PASSWORD = 'vqsh bfak ohnu dsgt'
EMAIL_HOST_USER = 'platraincloud@gmail.com'
EMAIL_HOST_PASSWORD = 'meczfpooichwkudl'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# PlatRain010

from django.contrib import admin

# Define the desired order for apps and their models
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

ADMIN_ORDERING = (
    ('about', (
        'CompanyInfo', 'CompanyInfoTranslation',
        # 'CompanyDescription', 'CompanyDescriptionTranslation',
        # 'SocialAccount',
        # 'Tech', 'TechTranslation',
        # 'TechUsage', 'TechUsageTranslation',
        # 'Policy', 'PolicyTranslation',
        # 'FinalProject'
    )),
    ('accounts', (
        'User', 'ParentStudent',
        'TeacherInfo', 'TeacherInfoTranslation',
        'TeacheroomAccount','ZoomAccount'
    )),
    # ('freemeet', ('FreeMeet',)),
    ('courses', (
        'Level', 'LevelTranslation',
        'Track', 'TrackTranslation',
        'Course', 'CourseTranslation',
        # 'LevelContent', 'LevelContentTranslation'
    )),
    ('library', (
        'CourseLibrary', 'MyLibrary',
    )),
    ('subscriptions', ('StudyGroup','JoinRequest','Lecture','StudyGroupResource','LectureVisitHistory')),
    # ('appointments', ('TeacherAvailability', 'Appointment')),
    # ('exams', ('Exam', 'Question', 'Option', 'ExamResult')),
    # ('orders', ('Order', 'OrderItem')),
    # ('loves', ('LoveTrack', 'LoveCourse')),
    # ('carts', ('CartLevel', 'CartTrack', 'CartCourse')),
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
        app_dict.values(), key=lambda x: [ao[0] for ao in ADMIN_ORDERING].index(x['app_label'])
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




CSRF_TRUSTED_ORIGINS = ['https://nabbiuwny.com','http://127.0.0.1:8000']
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
