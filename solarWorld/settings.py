import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from solarWorld.env import detect_environment, env_bool, env_int, env_list, env_str

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

ENVIRONMENT = detect_environment()
IS_PRODUCTION = ENVIRONMENT in {"prod", "production"}

FASTAPI_URLS = {
    "local": "http://localhost:8001",
    "prod": "http://fastapi-service:8000",
}

FASTAPI_URL = env_str(
    "FASTAPI_URL",
    FASTAPI_URLS["prod"] if IS_PRODUCTION else FASTAPI_URLS["local"],
)

# ЮKassa: тестовый магазин. Секреты задаются только через переменные окружения.
YOOKASSA_SHOP_ID = env_str("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = env_str("YOOKASSA_SECRET_KEY")
YOOKASSA_API_URL = env_str("YOOKASSA_API_URL", "https://api.yookassa.ru/v3")
PAYMENT_RETURN_URL = env_str("PAYMENT_RETURN_URL")
PAYMENT_TEST_MODE = env_bool("PAYMENT_TEST_MODE", default=True)
PAYMENT_REQUEST_TIMEOUT = env_int("PAYMENT_REQUEST_TIMEOUT", default=15)

SECRET_KEY = env_str("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY не задан. Добавьте его в .env для локального запуска "
        "или в переменные окружения на хостинге."
    )

DEBUG = env_bool("DEBUG", default=not IS_PRODUCTION)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

RENDER_EXTERNAL_HOSTNAME = env_str("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"],
)
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

USE_HTTPS = env_bool("USE_HTTPS", default=IS_PRODUCTION)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True

if USE_HTTPS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", default=3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        default=False,
    )
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=False)

# За прокси реальный IP приходит в X-Forwarded-For; локально заголовку не доверяем.
TRUST_PROXY_HEADERS = env_bool("TRUST_PROXY_HEADERS", default=IS_PRODUCTION)


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "planets",
    "accounts",
    "users",
    "shop",
]

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Solar World API",
    "DESCRIPTION": (
        "REST API каталога Solar World: планеты, спутники, миссии, "
        "агентства и компании. Основной эндпоинт каталога — /api/catalog/."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

# Включить: ENABLE_DEBUG_TOOLBAR=1.
ENABLE_DEBUG_TOOLBAR = os.getenv("ENABLE_DEBUG_TOOLBAR", "False").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(3, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "solarWorld.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "solarWorld.wsgi.application"


# Проект работает только с PostgreSQL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_str("DB_NAME", "solar_bd"),
        "USER": env_str("DB_USER", "postgres"),
        "PASSWORD": env_str("DB_PASSWORD", ""),
        "HOST": env_str("DB_HOST", "localhost"),
        "PORT": env_str("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}


# Кеширование с помощью Redis
REDIS_CACHE_OPTIONS = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
    # Без этого при недоступном Redis сайт падает с ConnectionError.
    "IGNORE_EXCEPTIONS": True,
    "SOCKET_CONNECT_TIMEOUT": 1,
    "SOCKET_TIMEOUT": 1,
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": REDIS_CACHE_OPTIONS,
        "KEY_PREFIX": "solar_world",
        "TIMEOUT": 60 * 15,
    }
}


# Password validation

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


# Internationalization

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


LOGIN_REDIRECT_URL = "profile"
LOGOUT_REDIRECT_URL = "main"

# На alwaysdata и в Docker нет отдельного веб-сервера для /static/.
if not DEBUG and "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }

if "test" in sys.argv or "pytest" in sys.modules:
    # В тестах Redis не нужен.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

if "RENDER" in os.environ:
    DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

    if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
        MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    STATIC_ROOT = BASE_DIR / "staticfiles"
