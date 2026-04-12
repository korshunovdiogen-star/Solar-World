import pytest
from django.urls import reverse
from django.test import Client
from planets.models import Planet

@pytest.mark.django_db
def test_catalog_api():
    # Создаём тестовые планеты
    Planet.objects.create(
        name="Марс",
        radius=3390,
        planet_type="terrestrial",
        order=4
    )
    Planet.objects.create(
        name="Венера",
        radius=6052,
        planet_type="terrestrial",
        order=2
    )
    Planet.objects.create(
        name="Юпитер",
        radius=69911,
        planet_type="gas_giant",
        order=5
    )

    client = Client()
    url = reverse('catalog_api')   # убедитесь, что в urls.py есть name='catalog_api'

    # 1. Без параметров – все объекты
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data
    assert len(data['results']) == 3
    assert data['total_pages'] == 1

    # 2. Фильтрация по категории 'planet'
    response = client.get(url, {'category': 'planet'})
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 3

    # 3. Поиск по названию
    response = client.get(url, {'q': 'Марс'})
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 1
    assert data['results'][0]['name'] == 'Марс'

    # 4. Сортировка по радиусу по убыванию
    response = client.get(url, {'ordering': 'radius_desc'})
    assert response.status_code == 200
    data = response.json()
    radii = [item['radius'] for item in data['results']]
    assert radii == sorted(radii, reverse=True)