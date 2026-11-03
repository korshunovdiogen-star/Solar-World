from datetime import date

import pytest
from django.test import Client
from django.urls import reverse

from planets.models import Mission, Planet, SpaceAgency


@pytest.mark.django_db
def test_all_catalog_uses_lightweight_card_serializer():
    planet = Planet.objects.create(
        name='Марс',
        radius=3390,
        planet_type='TER',
        order=4,
        text='Первая строка.\nВторая строка.',
        image='planets/mars.jpg',
    )

    response = Client().get(reverse('catalog_api'))

    assert response.status_code == 200
    item = next(
        result for result in response.json()['results']
        if result['model_type'] == 'planet'
    )

    assert item['id'] == planet.pk
    assert item['name'] == 'Марс'
    assert item['first_line'] == 'Первая строка.'
    assert item['image'] == '/media/planets/mars.jpg'
    assert item['detail_url'] == f'/planet/{planet.pk}/'
    assert item['type_display'] == 'Земная группа'
    assert item['radius'] == 3390

    # Полное описание и вложенные объекты в карточку не попадают.
    assert 'text' not in item
    assert 'remaining_text' not in item
    assert 'satellites' not in item


@pytest.mark.django_db
def test_all_catalog_card_includes_mission_agencies():
    agency = SpaceAgency.objects.create(
        name='NASA',
        country='США',
        established_date=date(1958, 7, 29),
        text='Американское космическое агентство.',
    )
    mission = Mission.objects.create(
        name='Аполлон',
        mission_type='MRV',
        launch_date=date(1969, 7, 16),
        text='Первая строка миссии.\nОстальной текст.',
    )
    mission.space_agency.add(agency)

    response = Client().get(reverse('catalog_api'))
    item = next(
        result for result in response.json()['results']
        if result['model_type'] == 'mission'
    )

    assert item['first_line'] == 'Первая строка миссии.'
    assert item['agency_names'] == ['NASA']
    assert 'radius' not in item


@pytest.mark.django_db
def test_category_catalog_also_returns_lightweight_cards():
    Planet.objects.create(
        name='Венера',
        radius=6052,
        planet_type='TER',
        order=2,
        text='Первая строка Венеры.\nОстальной текст.',
    )

    response = Client().get(reverse('catalog_api'), {'category': 'planet'})
    item = response.json()['results'][0]

    assert item['first_line'] == 'Первая строка Венеры.'
    assert 'text' not in item
    assert 'remaining_text' not in item
