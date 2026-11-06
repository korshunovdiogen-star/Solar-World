from datetime import date

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse

from planets.models import Company, Planet
from users.models import Favorite


@pytest.fixture
def locmem_cache(monkeypatch):
    cache = LocMemCache("detail-tests", {})
    monkeypatch.setattr("planets.views.cache", cache)
    return cache


@pytest.fixture
def planet(db):
    return Planet.objects.create(
        name="Марс",
        order=4,
        radius=3390,
        planet_type="TER",
        text="Марс — четвёртая планета.\nИнтересный факт: ...",
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.mark.django_db
def test_cached_detail_does_not_hide_user_favorite(client, user, planet, locmem_cache):
    """Аноним прогревает кеш, но авторизованный всё равно видит свой флаг."""
    content_type = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=content_type, object_id=planet.id)
    url = reverse("planet_detail", args=[planet.id])

    response = client.get(url)
    assert response.context["is_favorite"] is False

    client.force_login(user)
    response = client.get(url)
    assert response.context["is_favorite"] is True


@pytest.mark.django_db
def test_cached_detail_does_not_leak_favorite_to_anonymous(client, user, planet, locmem_cache):
    """Флаг одного пользователя не должен попадать в кеш для всех остальных."""
    content_type = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=content_type, object_id=planet.id)
    url = reverse("planet_detail", args=[planet.id])

    client.force_login(user)
    response = client.get(url)
    assert response.context["is_favorite"] is True

    client.logout()
    response = client.get(url)
    assert response.context["is_favorite"] is False


@pytest.mark.django_db
def test_detail_cache_does_not_store_is_favorite(client, planet, locmem_cache):
    """В общем кеше не должно быть личного флага."""
    client.get(reverse("planet_detail", args=[planet.id]))

    cached = locmem_cache.get(f"planet:{planet.id}:detail")
    assert cached is not None
    assert "is_favorite" not in cached


@pytest.mark.django_db
def test_detail_page_sets_csrf_cookie(client, planet, locmem_cache):
    """Кнопке избранного нужен CSRF-токен, поэтому cookie должна появляться."""
    response = client.get(reverse("planet_detail", args=[planet.id]))

    assert "csrftoken" in response.cookies
    assert 'name="csrf-token"' in response.content.decode()


@pytest.mark.django_db
def test_company_detail_includes_is_favorite(client, user, locmem_cache):
    """У компании флаг тоже должен попадать в контекст."""
    company = Company.objects.create(
        name="Тестовая компания",
        country="Россия",
        established_date=date(2020, 1, 1),
        text="Первая строка.\nОстальной текст.",
    )
    content_type = ContentType.objects.get_for_model(Company)
    Favorite.objects.create(user=user, content_type=content_type, object_id=company.id)

    client.force_login(user)
    response = client.get(reverse("company_detail", args=[company.id]))

    assert response.status_code == 200
    assert response.context["is_favorite"] is True
