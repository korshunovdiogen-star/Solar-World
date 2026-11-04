import hashlib

from django.conf import settings
from django.core.cache import cache


# Сколько неудачных попыток разрешено и на сколько минут блокируем.
LOGIN_IP_LIMIT = 20
LOGIN_USER_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60


def get_client_ip(request):
    """
    Возвращает IP посетителя.

    На хостинге сайт обычно стоит за прокси, и настоящий IP приходит
    в заголовке X-Forwarded-For. Локально этому заголовку не доверяем,
    чтобы его нельзя было подделать.
    """
    if getattr(settings, 'TRUST_PROXY_HEADERS', False):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', 'unknown')


def _key(scope, value):
    # В ключе не храним логин и IP открытым текстом.
    digest = hashlib.sha256(value.encode('utf-8')).hexdigest()[:32]
    return f'rate-limit:{scope}:{digest}'


def get_count(scope, value):
    """Сколько неудачных попыток уже записано."""
    # Если Redis временно недоступен, cache.get вернёт None.
    return cache.get(_key(scope, value), 0) or 0


def is_limited(scope, value, limit):
    """True, если попыток уже набралось на блокировку."""
    # Если Redis временно недоступен, считаем, что блокировки нет,
    # и сайт продолжает работать.
    return get_count(scope, value) >= limit


def register_failure(scope, value):
    """Считает одну неудачную попытку и возвращает новое число."""
    key = _key(scope, value)

    # Первая попытка создаёт ключ сразу с нужным сроком жизни.
    if cache.add(key, 1, timeout=LOGIN_WINDOW_SECONDS):
        return 1

    try:
        return cache.incr(key)
    except ValueError:
        # Ключ успел истечь между add и incr — начинаем счёт заново.
        cache.set(key, 1, timeout=LOGIN_WINDOW_SECONDS)
        return 1


def reset(scope, value):
    """Сбрасывает счётчик после успешного входа."""
    cache.delete(_key(scope, value))
