from pathlib import Path
import os
import pymysql


BASE_DIR = Path(__file__).resolve().parent.parent

#SECRET_KEY =env('SECRET_KEY')
SECRET_KEY = "django-insecure-+a&_h)1p4ert$nm!%@8t$ie^qku11#$+qqk&5$v%$-ft4tv%g*"
DEBUG =False 

ALLOWED_HOSTS = ['*', "localhost", "50.19.183.215"]


INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'accounts.apps.AccountsConfig',
    'about.apps.AboutConfig',
    'studyclass.apps.StudyclassConfig',
    'quizv4.apps.Quizv4Config',
    'assignment.apps.AssignmentConfig',
    'presence.apps.PresenceConfig',
    'emptyhall.apps.EmptyhallConfig',
    'settings.apps.SettingsConfig',
    'chat.apps.ChatConfig',
    "crispy_forms",
    "crispy_bootstrap5",
    'rest_framework',
    
]


ASGI_APPLICATION = 'project.asgi.application'

CHANNEL_LAYERS = {
    'default':{
        'BACKEND':'channels.layers.InMemoryChannelLayer'
    }
}

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
]
ROOT_URLCONF = 'project.urls'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

AUTHENTICATION_BACKENDS = [
    'accounts.authentication.CustomAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# Security settings
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
MAX_UPLOAD_SIZE = 2147483648  # 2GB in bytes

BUNNY_API_KEY = '49bb89fe-807d-4586-9ce6-e29bdaa7a550ab26bc71-4760-4afa-bb59-94bea08ceb75'
base_url = 'https://api.bunny.net'
base_url_2='https://video.bunnycdn.com'


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
                'about.arabic_context_processor.languageswitcher',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),  # Default to 'bluebook' if not set
        'USER': os.getenv('DB_USER'),      # Default to 'root' if not set
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Default to 'haitham' if not set
        'HOST': os.getenv('DB_HOST'),     # Default to 'mysql' if not set
        'PORT': os.getenv('DB_PORT'),      # Default to '3306' if not set
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
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]

# Define STATIC_ROOT for collectstatic to gather files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = "/media/"
#MEDIA_ROOT = BASE_DIR/"media"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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
EMAIL_HOST_USER = 'platraincloud@gmail.com'
EMAIL_HOST_PASSWORD = 'meczfpooichwkudl'
# PlatRain010


from django.contrib import admin

ADMIN_ORDERING = (
    ('studyclass', ('Subject', 'SubjectFile', 'Lecture', 'LectureFile')),
    ('quizv4', ('Question',)),
    # ('assignment', ('Assignment',)),
    ('accounts', ('User', 'Following', 'OwnerAccount')),
    ('auth', ('Group', )),
    ('sessions', ('Session', )),
    ('admin_interface', ('Theme', )),
)


def get_app_list(self, request, app_label=None):
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
                if not model['object_name'] in ao[1]:
                    app['models'].remove(model)
        app['models'].sort(key=lambda x: ao[1].index(x['object_name']))
    return app_list

admin.AdminSite.get_app_list = get_app_list
CSRF_TRUSTED_ORIGINS = ['https://bluebook.iceage.me.uk']
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
