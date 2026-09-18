from datetime import timedelta
from pathlib import Path

from decouple import Csv, config
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY: str = config("SECRET_KEY", default="")
DEBUG = config("DEBUG", default="True") == "True"
ALLOWED_HOSTS: list = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
WSGI_APPLICATION = "cinema.wsgi.application"
ROOT_URLCONF = "cinema.urls"
AUTH_USER_MODEL = "users.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.google.GoogleOAuth2",
]
SOCIAL_AUTH_USER_MODEL = "users.CustomUser"
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["openid", "email", "profile"]
SOCIAL_AUTH_PIPELINE = [
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_by_email",
    "users.social_pipeline.create_or_update_social_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
]
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ["email"]
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = "/"
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "social_django", 
]

LOCAL_APPS = [
    "users.apps.UsersConfig",
    "movies.apps.MoviesConfig",
    "streaming.apps.StreamingConfig",
    "reviews.apps.ReviewsConfig",
    "search.apps.SearchConfig",
    "payments.apps.PaymentsConfig",
    "pages",
    "watchlist",
    "toplamlar",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.global_context",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="cinemadb"),
        "USER": config("POSTGRES_USER", default="myuser"),
        "PASSWORD": config("POSTGRES_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default=5432, cast=int),
        "CONN_MAX_AGE": 60,
    }
}


REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "TIMEOUT": 300,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
        "KEY_PREFIX": "cinema",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1_209_600
SESSION_COOKIE_HTTPONLY = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "EXCEPTION_HANDLER": "utils.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AWS_ACCESS_KEY_ID: str = config("MINIO_ACCESS_KEY", default="")
AWS_SECRET_ACCESS_KEY: str = config("MINIO_SECRET_KEY", default="")
AWS_STORAGE_BUCKET_NAME: str = config("MINIO_BUCKET_NAME", default="cinema")
AWS_S3_ENDPOINT_URL: str = config("MINIO_ENDPOINT", default="http://localhost:9000")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = False

# Email sozlamalari
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default='True') == 'True'
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@cinema.uz')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:8000')

PAYMENT_PROVIDER = config('PAYMENT_PROVIDER', default='manual')
PAYMENT_WEBHOOK_SECRET = config('PAYMENT_WEBHOOK_SECRET', default='')
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')
PAYME_MERCHANT_ID = config('PAYME_MERCHANT_ID', default='')
PAYME_SECRET_KEY = config('PAYME_SECRET_KEY', default='')
PAYME_BASE_URL = config('PAYME_BASE_URL', default='https://checkout.paycom.uz')

CORS_ALLOWED_ORIGINS: list = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:8000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

JAZZMIN_SETTINGS = {
    "site_title": "Cinema Admin",
    "site_header": "Cinema",
    "site_brand": "🎬 Cinema.uz",
    "welcome_sign": "Cinema boshqaruv paneli",
    "copyright": "Cinema.uz",
    "show_ui_builder": False,
}

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}:{lineno} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
        },
    },
    "root": {
        "handlers": ["console", "file_error"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "users":  {"handlers": ["console"], "level": "INFO", "propagate": False},
        "movies": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
CSRF_TRUSTED_ORIGINS: list = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000",
    cast=Csv(),
)

# ⚠️ HTTPS/secure-cookie sozlamalari `production.py` da boshqariladi
# (SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE).
# base.py da majburiy yoqilsa, local HTTP muhitida cheksiz redirect bo'ladi.

USE_X_FORWARDED_HOST = True
