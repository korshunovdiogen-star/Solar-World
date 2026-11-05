import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from solarWorld.env import detect_environment, env_bool, env_int, env_list, env_str



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# Окружение определяется автоматически:
# - ENVIRONMENT из .env или переменных окружения имеет приоритет;
# - на Render/Railway/Heroku окружение считается production;
# - во всех остальных случаях — local.
ENVIRONMENT = detect_environment()
IS_PRODUCTION = ENVIRONMENT in {'prod', 'production'}

FASTAPI_URLS = {
    'local': 'http://localhost:8001',
    'prod': 'http://fastapi-service:8000',
}

FASTAPI_URL = env_str(
    'FASTAPI_URL',
    FASTAPI_URLS['prod'] if IS_PRODUCTION else FASTAPI_URLS['local'],
)

SECRET_KEY = env_str('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY не задан. Добавьте его в .env для локального запуска '
        'или в переменные окружения на хостинге.'
    )

# Локально DEBUG включён, на хостинге — выключен.
# Явное значение DEBUG в .env или окружении имеет приоритет.
DEBUG = env_bool('DEBUG', default=not IS_PRODUCTION)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Домены: локальные по умолчанию, на Render внешний домен добавляется сам.
RENDER_EXTERNAL_HOSTNAME = env_str('RENDER_EXTERNAL_HOSTNAME')

ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1', '[::1]'],
)
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# HTTPS включается автоматически в production. Локально остаётся http.
# При необходимости можно переопределить через USE_HTTPS.
USE_HTTPS = env_bool('USE_HTTPS', default=IS_PRODUCTION)

# Безопасные заголовки. Django включает часть из них по умолчанию,
# но явные настройки понятнее и не зависят от версии.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True

if USE_HTTPS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', default=3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        default=False,
    )
    SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', default=False)

# На хостинге сайт работает за прокси, поэтому реальный IP посетителя
# приходит в заголовке X-Forwarded-For. Локально заголовку не доверяем.
TRUST_PROXY_HEADERS = env_bool('TRUST_PROXY_HEADERS', default=IS_PRODUCTION)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'planets',
    'users',
    'shop',
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

INTERNAL_IPS = ['127.0.0.1']

# Debug Toolbar выключен по умолчанию. Включить: ENABLE_DEBUG_TOOLBAR=1 в .env или окружении.
ENABLE_DEBUG_TOOLBAR = os.getenv('ENABLE_DEBUG_TOOLBAR', 'False').strip().lower() in ('1', 'true', 'yes', 'on')

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(3, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'solarWorld.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'solarWorld.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


def _is_running_tests():
    """True, если код запущен тестами. Тесты всегда идут на SQLite."""
    if 'pytest' in sys.modules:
        return True
    return len(sys.argv) > 1 and sys.argv[1] == 'test'


# База выбирается через .env:
# - DB_ENGINE не задан или равен sqlite3 — используется demo_data/db.sqlite3;
# - DB_ENGINE=django.db.backends.postgresql — PostgreSQL из DB_* ниже.
# Тесты всегда работают на SQLite, чтобы не трогать рабочую базу.
DB_ENGINE = env_str('DB_ENGINE', 'django.db.backends.sqlite3')

# Демо-база и фикстура лежат в demo_data/ — это данные учебного проекта,
# а не рабочие данные. См. demo_data/README.md.
SQLITE_DB_PATH = BASE_DIR / 'demo_data' / 'db.sqlite3'

if _is_running_tests() or DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': SQLITE_DB_PATH,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': env_str('DB_NAME', 'solar_bd'),
            'USER': env_str('DB_USER', 'postgres'),
            'PASSWORD': env_str('DB_PASSWORD', ''),
            'HOST': env_str('DB_HOST', 'localhost'),
            'PORT': env_str('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }


# Кеширование с помощью Redis
REDIS_CACHE_OPTIONS = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
    # Если Redis недоступен, сайт продолжает работать без кеша,
    # а не падает с ConnectionError.
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

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS=[
    BASE_DIR / "static"
    ]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


LOGIN_REDIRECT_URL = 'profile'   # после входа - в профиль
LOGOUT_REDIRECT_URL = 'main'  # после выхода - на главную

# WhiteNoise раздаёт статику, когда DEBUG выключен: на alwaysdata и в Docker
# нет отдельного веб-сервера для /static/, поэтому без него сайт открывается
# без CSS, JS и картинок.
if not DEBUG and 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }

if 'test' in sys.argv or 'pytest' in sys.modules:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Настройки для Render (применяются, только если проект запущен в облаке)
if 'RENDER' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }

    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATIC_ROOT = BASE_DIR / 'staticfiles'
