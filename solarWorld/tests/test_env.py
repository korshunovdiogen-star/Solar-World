import pytest
from django.core.exceptions import ImproperlyConfigured

from solarWorld.env import detect_environment, env_bool, env_int, env_list, env_str


def test_env_str_strips_and_uses_default(monkeypatch):
    monkeypatch.setenv('SOLAR_TEST_STR', '  value  ')
    assert env_str('SOLAR_TEST_STR') == 'value'

    monkeypatch.setenv('SOLAR_TEST_STR', '   ')
    assert env_str('SOLAR_TEST_STR', 'fallback') == 'fallback'


@pytest.mark.parametrize('value', ['1', 'true', 'YES', 'on'])
def test_env_bool_true_values(monkeypatch, value):
    monkeypatch.setenv('SOLAR_TEST_BOOL', value)
    assert env_bool('SOLAR_TEST_BOOL') is True


@pytest.mark.parametrize('value', ['0', 'false', 'no', 'off', ''])
def test_env_bool_false_values(monkeypatch, value):
    monkeypatch.setenv('SOLAR_TEST_BOOL', value)
    assert env_bool('SOLAR_TEST_BOOL') is False


def test_env_bool_missing_uses_default(monkeypatch):
    monkeypatch.delenv('SOLAR_TEST_BOOL', raising=False)
    assert env_bool('SOLAR_TEST_BOOL', default=True) is True


def test_env_int(monkeypatch):
    monkeypatch.setenv('SOLAR_TEST_INT', '8001')
    assert env_int('SOLAR_TEST_INT') == 8001


def test_env_int_invalid_value(monkeypatch):
    monkeypatch.setenv('SOLAR_TEST_INT', 'not-a-number')
    with pytest.raises(ImproperlyConfigured):
        env_int('SOLAR_TEST_INT')


def test_env_list(monkeypatch):
    monkeypatch.setenv('SOLAR_TEST_LIST', 'localhost, 127.0.0.1, ,example.com')
    assert env_list('SOLAR_TEST_LIST') == ['localhost', '127.0.0.1', 'example.com']


def test_env_list_missing_uses_default(monkeypatch):
    monkeypatch.delenv('SOLAR_TEST_LIST', raising=False)
    assert env_list('SOLAR_TEST_LIST', default=['localhost']) == ['localhost']


def test_detect_environment_explicit(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'PROD')
    assert detect_environment() == 'prod'


def test_detect_environment_render(monkeypatch):
    monkeypatch.delenv('ENVIRONMENT', raising=False)
    monkeypatch.setenv('RENDER', 'true')
    assert detect_environment() == 'prod'


def test_detect_environment_local(monkeypatch):
    for marker in ('ENVIRONMENT', 'RENDER', 'RAILWAY_ENVIRONMENT', 'DYNO'):
        monkeypatch.delenv(marker, raising=False)
    assert detect_environment() == 'local'
