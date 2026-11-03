import pytest
import requests
from django.core.cache.backends.locmem import LocMemCache
from types import SimpleNamespace

from planets import utils
from planets.models import Planet


@pytest.fixture
def locmem_cache(monkeypatch):
    cache = LocMemCache('utils-tests', {})
    cache.clear()
    monkeypatch.setattr(utils, 'cache', cache)
    return cache


@pytest.mark.django_db
def test_fastapi_failure_is_negative_cached(monkeypatch, locmem_cache):
    """При падении FastAPI повторный запрос не уходит на каждую загрузку страницы."""
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        raise requests.exceptions.ConnectionError('FastAPI недоступен')

    monkeypatch.setattr(utils.requests, 'get', fake_get)

    assert utils.get_daily_planet_from_microservice() is None
    assert utils.get_daily_planet_from_microservice() is None

    assert len(calls) == 1
    assert locmem_cache.get(utils.NEGATIVE_CACHE_KEY) is True


@pytest.mark.django_db
def test_successful_fastapi_response_fills_positive_cache(monkeypatch, locmem_cache):
    planet = Planet.objects.create(
        name='Марс',
        radius=3390,
        planet_type='TER',
        order=4,
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {'planet_id': planet.pk}

    monkeypatch.setattr(utils.requests, 'get', lambda *args, **kwargs: FakeResponse())

    result = utils.get_daily_planet_from_microservice()

    assert result is not None
    assert result.pk == planet.pk
    assert locmem_cache.get(utils.CACHE_KEY) == planet.pk
    assert locmem_cache.get(utils.NEGATIVE_CACHE_KEY) is None


def test_separate_first_line_handles_empty_text():
    assert utils.separate_first_line(SimpleNamespace(text=None)) == ('', '')
    assert utils.separate_first_line(SimpleNamespace(text='')) == ('', '')


def test_separate_first_line_splits_text():
    obj = SimpleNamespace(text='Первая строка.\nВторая строка.\nТретья.')

    assert utils.separate_first_line(obj) == (
        'Первая строка.',
        'Вторая строка.\nТретья.',
    )
