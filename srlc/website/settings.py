import os,sentry_sdk,environ
from pathlib import Path
from sentry_sdk.integrations.django import DjangoIntegration

## REMOVE OR COMMENT OUT THESE LINES IF YOU WANT TO DISABLE SENTRY/GLITCHTIP.
sentry_sdk.init(
    dsn                     = os.getenv("SENTRY_DSN"),
    integrations            = [DjangoIntegration()],
    auto_session_tracking   = False,
    traces_sample_rate      = 1.0,
    profiles_sample_rate    = 1.0,
    release                 = "2.2.0",
    environment             = "development",
)

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = ["localhost","127.0.0.1","django"]
#ALLOWED_IPS = ["127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    # PRE-INSTALLED
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # THIRD-PARTY
    "corsheaders",
    "rest_framework",
    "rest_framework_api_key",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_bootstrap5",
    "sekizai",
    # LOCAL
    "srl",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "website.urls"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

TEMPLATES = [
    {
        "BACKEND"       : "django.template.backends.django.DjangoTemplates",
        "DIRS"          : [],
        "APP_DIRS"      : True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework_api_key.permissions.HasAPIKey",
    ],
}

WSGI_APPLICATION = "website.wsgi.application"

if os.getenv("DEBUG_MODE") or True:
    print("DEBUG ENABLED!!!!! MAKE SURE YOU AREN'T IN PRODUCTION!!!!!")
    DEBUG = True
    
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(PROJECT_DIR, "sqlite3.db"),
        }
    }
else:
    # Security Setttings
    CSRF_COOKIE_SECURE              = True
    SESSION_COOKIE_SECURE           = True
    SECURE_SSL_REDIRECT             = False ## ASSUMES YOU ARE USING NPM
    SECURE_HSTS_SECONDS             = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
    SECURE_HSTS_PRELOAD             = True
    SECURE_SSL_HOST                 = False ## ASSUMES YOU ARE USING NPM
    SECURE_CONTENT_TYPE_NOSNIFF     = True
    SECURE_BROWSER_XSS_FILTER       = True
    X_FRAME_OPTIONS                 = "DENY"
    SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https')

    DATABASES = {
        "default": {
            "ENGINE"    : "django.db.backends.postgresql",
            "NAME"      : os.getenv("POSTGRES_NAME"),
            "USER"      : os.getenv("POSTGRES_USER"),
            "PASSWORD"  : os.getenv("POSTGRES_PASSWORD"),
            "HOST"      : "postgres",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# API RATE LIMITING
RATELIMIT_RATE      = "50/m"
RATELIMIT_RESPONSE  = '{"error": "Too many requests. Please try again later."}'
RATELIMIT_ENABLE    = True


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE   = "en-us"
TIME_ZONE       = "UTC"
USE_I18N        = True
USE_TZ          = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

PROJECT_DIR     = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT     = os.path.join(PROJECT_DIR, 'static')
STATIC_URL      = "website/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"