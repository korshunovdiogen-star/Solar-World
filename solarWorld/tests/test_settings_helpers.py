import pytest

from django.conf import settings

from solarWorld.utils import parse_page_number


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('1', 1),
        ('5', 5),
        ('abc', 1),
        ('', 1),
        ('0', 1),
        ('-3', 1),
        (None, 1),
    ],
)
def test_parse_page_number(value, expected):
    assert parse_page_number(value) == expected


def test_redis_cache_ignores_connection_errors():
    """Redis не должен ронять сайт, если он временно недоступен."""
    assert settings.REDIS_CACHE_OPTIONS['IGNORE_EXCEPTIONS'] is True


def test_security_headers_are_enabled():
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.X_FRAME_OPTIONS == 'DENY'
    assert settings.SECURE_REFERRER_POLICY == 'same-origin'
    assert settings.SESSION_COOKIE_HTTPONLY is True
