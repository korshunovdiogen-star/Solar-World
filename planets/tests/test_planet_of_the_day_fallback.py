import pytest
from django.template import Context, Template
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_planet_of_the_day_redirects_to_main_when_microservice_is_down(monkeypatch):
    monkeypatch.setattr(
        'planets.views.get_daily_planet_from_microservice',
        lambda: None,
    )

    response = Client().get(reverse('planet_of_the_day'))

    assert response.status_code == 302
    assert response.url == reverse('main')


@pytest.mark.django_db
def test_main_page_hides_daily_planet_card_when_microservice_is_down(monkeypatch):
    monkeypatch.setattr(
        'planets.views.get_daily_planet_from_microservice',
        lambda: None,
    )

    response = Client().get(reverse('main'))

    assert response.status_code == 200
    assert 'Планета дня' not in response.content.decode()


def test_versioned_static_adds_file_modification_time():
    rendered = Template(
        "{% load rich_text %}{% versioned_static 'css/catalog.css' %}"
    ).render(Context({}))

    assert 'css/catalog.css?v=' in rendered
    version = rendered.rsplit('?v=', 1)[1]
    assert version.isdigit()


def test_versioned_static_keeps_plain_url_for_missing_file():
    rendered = Template(
        "{% load rich_text %}{% versioned_static 'css/no-such-file.css' %}"
    ).render(Context({}))

    assert rendered.endswith('css/no-such-file.css')
    assert '?v=' not in rendered
