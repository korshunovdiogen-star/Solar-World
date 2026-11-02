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
        planet_type="TER",
        order=4
    )
    Planet.objects.create(
        name="Венера",
        radius=6052,
        planet_type="TER",
        order=2
    )
    Planet.objects.create(
        name="Юпитер",
        radius=69911,
        planet_type="GAS",
        order=5
    )

    client = Client()
    url = reverse('catalog_api')

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
    response = client.get(url, {'category': 'planet', 'ordering': 'radius_desc'})
    assert response.status_code == 200
    data = response.json()
    radii = [item['radius'] for item in data['results']]
    assert radii == sorted(radii, reverse=True)


# API только для чтения: данные редактируются в админке, а не через API.
READ_ONLY_ENDPOINTS = [
    '/api/planets/',
    '/api/satellites/',
    '/api/missions/',
    '/api/agencies/',
    '/api/companies/',
]


@pytest.mark.django_db
@pytest.mark.parametrize('url', READ_ONLY_ENDPOINTS)
def test_api_list_is_read_only(url):
    """Список отдаётся по GET, а запись недоступна даже анонимному клиенту."""
    client = Client()

    assert client.get(url).status_code == 200

    for method in ('post', 'put', 'patch', 'delete'):
        response = getattr(client, method)(url, data={}, content_type='application/json')
        assert response.status_code == 405, f'{method.upper()} {url} должен возвращать 405'


@pytest.mark.django_db
def test_api_detail_is_read_only():
    """Детальный эндпоинт тоже не даёт изменить или удалить объект."""
    planet = Planet.objects.create(
        name="Тестовая планета",
        radius=1000,
        planet_type="TER",
        order=99,
    )
    client = Client()
    url = f'/api/planets/{planet.pk}/'

    assert client.get(url).status_code == 200

    for method in ('post', 'put', 'patch', 'delete'):
        response = getattr(client, method)(url, data={}, content_type='application/json')
        assert response.status_code == 405, f'{method.upper()} {url} должен возвращать 405'

    # Объект не изменился и не удалился.
    planet.refresh_from_db()
    assert planet.name == "Тестовая планета"