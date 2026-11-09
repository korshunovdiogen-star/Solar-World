import hashlib

from django.conf import settings
from django.core.cache import cache

LOGIN_IP_LIMIT = 20
LOGIN_USER_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60


def get_client_ip(request):
    """IP посетителя; X-Forwarded-For учитывается только при TRUST_PROXY_HEADERS."""
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "unknown")


def _key(scope, value):
    # В ключе не храним логин и IP открытым текстом.
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]
    return f"rate-limit:{scope}:{digest}"


def get_count(scope, value):
    return cache.get(_key(scope, value), 0) or 0


def is_limited(scope, value, limit):
    # Если Redis недоступен, cache.get вернёт None и сайт продолжит работать.
    return get_count(scope, value) >= limit


def register_failure(scope, value):
    key = _key(scope, value)

    # Первая попытка создаёт ключ сразу с нужным сроком жизни.
    if cache.add(key, 1, timeout=LOGIN_WINDOW_SECONDS):
        return 1

    try:
        return cache.incr(key)
    except ValueError:
        # Ключ истёк между add и incr — начинаем счёт заново.
        cache.set(key, 1, timeout=LOGIN_WINDOW_SECONDS)
        return 1


def reset(scope, value):
    cache.delete(_key(scope, value))
