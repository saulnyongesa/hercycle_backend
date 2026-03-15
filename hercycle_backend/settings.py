
from pathlib import Path

import django_heroku

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=ps@cleqvs1smtp2%#*-2tngz+k(0x+*nq@dg^vd+0cvi3x_v#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',    
    'rest_framework',
    'core',
    'api',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hercycle_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],  # Global templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hercycle_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 1. For the Mobile App (HemaCycle Android)
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        
        # 2. Add this back! For the Web Dashboards (CHVs & Admins)
        'rest_framework.authentication.SessionAuthentication',
        
        # (Optional) Helpful if you are testing endpoints directly in the browser
        'rest_framework.authentication.BasicAuthentication',
    ),
    
    # ... keep your existing pagination and renderer settings here ...
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'api.renderers.EnvelopeJSONRenderer',
    # ),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'HemaCycle Mobile API',
    'DESCRIPTION': 'Version 1 of the offline-first API for HemaCycle mobile apps.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

if not DEBUG:
    # Local Development Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CKEditor 5 Configuration for your specific features
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'fontFamily', 'fontColor', 'alignment', '|',
            'bulletedList', 'numberedList', 'blockQuote', 'codeBlock', '|',
            'imageUpload', 'insertTable', 'link', '|', 'undo', 'redo'
        ],
        'codeBlock': {
            'languages': [
                {'language': 'plaintext', 'label': 'Plain text'},
                {'language': 'bash', 'label': 'Bash'},
                {'language': 'python', 'label': 'Python'},
                {'language': 'html', 'label': 'HTML'},
                {'language': 'css', 'label': 'CSS'},
                {'language': 'javascript', 'label': 'JavaScript'}
            ]
        },
        'height': 400,
        'width': '100%',
    }
}
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "any"

AUTH_USER_MODEL = 'core.User'
django_heroku.settings(locals())