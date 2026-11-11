import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from planets.models import Planet
from users.models import Favorite, History, Profile

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def planet():
    return Planet.objects.create(
        name="Марс",
        order=4,
        radius=3390,
        planet_type="TER",
        text="Марс — четвёртая планета.\nИнтересный факт: ...",
    )


@pytest.mark.django_db
def test_register_view_get(client):
    url = reverse("register")
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_register_view_post_success(client):
    url = reverse("register")
    data = {
        "username": "newuser",
        "password1": "complex_password_123",
        "password2": "complex_password_123",
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("main")
    assert User.objects.filter(username="newuser").exists()
    new_user = User.objects.get(username="newuser")
    assert Profile.objects.filter(user=new_user).exists()


@pytest.mark.django_db
def test_register_view_post_invalid(client):
    url = reverse("register")
    data = {"username": "newuser", "password1": "pass", "password2": "different"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["form"].errors
    assert not User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_login_view(client, user):
    url = reverse("login")
    data = {"username": "testuser", "password": "testpass"}
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("profile")


@pytest.mark.django_db
def test_logout_view(client, user):
    client.login(username="testuser", password="testpass")
    url = reverse("logout")
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("main")


@pytest.mark.django_db
def test_profile_view_requires_login(client):
    url = reverse("profile")
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


@pytest.mark.django_db
def test_profile_view_authenticated(client, user):
    client.login(username="testuser", password="testpass")
    url = reverse("profile")
    response = client.get(url)
    assert response.status_code == 200
    assert "user" in response.context
    assert response.context["user"] == user


@pytest.mark.django_db
def test_profile_prefetches_favorite_objects(client, user, planet, django_assert_num_queries):
    """Объекты избранного подгружаются заранее, без запроса на каждую строку."""
    content_type = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=content_type, object_id=planet.id)
    client.login(username="testuser", password="testpass")

    response = client.get(reverse("profile"))
    favorites = list(response.context["article_favorites"])

    with django_assert_num_queries(0):
        assert [favorite.content_object.name for favorite in favorites] == [planet.name]


@pytest.mark.django_db
def test_toggle_favorite_add(client, user, planet):
    client.login(username="testuser", password="testpass")
    url = reverse("toggle_favorite")
    data = {"content_type": "planet", "object_id": planet.id}
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["is_favorite"] is True
    ct = ContentType.objects.get_for_model(Planet)
    assert Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()


@pytest.mark.django_db
def test_toggle_favorite_remove(client, user, planet):
    ct = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)
    client.login(username="testuser", password="testpass")
    url = reverse("toggle_favorite")
    data = {"content_type": "planet", "object_id": planet.id}
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["is_favorite"] is False
    assert not Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()


@pytest.mark.django_db
def test_toggle_favorite_unauthenticated(client, planet):
    url = reverse("toggle_favorite")
    data = {"content_type": "planet", "object_id": planet.id}
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 302


@pytest.mark.django_db
def test_toggle_favorite_requires_post(client, user, planet):
    client.login(username="testuser", password="testpass")
    response = client.get(reverse("toggle_favorite"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_toggle_favorite_requires_csrf(user, planet):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    data = {"content_type": "planet", "object_id": planet.id}
    response = client.post(
        reverse("toggle_favorite"),
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_toggle_favorite_invalid_json(client, user, planet):
    client.login(username="testuser", password="testpass")
    response = client.post(
        reverse("toggle_favorite"),
        "{not json",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_toggle_favorite_unknown_object(client, user):
    client.login(username="testuser", password="testpass")
    data = {"content_type": "planet", "object_id": 999999}
    response = client.post(
        reverse("toggle_favorite"),
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_favorite_endpoints_require_post(client, user, planet):
    client.login(username="testuser", password="testpass")
    add_url = reverse("add_favorite", args=["planet", planet.id])
    remove_url = reverse("remove_favorite", args=["planet", planet.id])
    assert client.get(add_url).status_code == 405
    assert client.get(remove_url).status_code == 405


@pytest.mark.django_db
def test_add_and_remove_favorite_post(client, user, planet):
    client.login(username="testuser", password="testpass")
    ct = ContentType.objects.get_for_model(Planet)
    add_url = reverse("add_favorite", args=["planet", planet.id])
    remove_url = reverse("remove_favorite", args=["planet", planet.id])

    assert client.post(add_url).status_code == 302
    assert Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()

    assert client.post(remove_url).status_code == 302
    assert not Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()


@pytest.mark.django_db
def test_add_favorite_rejects_unknown_object(client, user):
    client.login(username="testuser", password="testpass")
    response = client.post(reverse("add_favorite", args=["planet", 999999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_favorite_redirect_ignores_external_referer(client, user, planet):
    client.login(username="testuser", password="testpass")
    url = reverse("add_favorite", args=["planet", planet.id])
    response = client.post(url, HTTP_REFERER="https://evil.example/phish")
    assert response.status_code == 302
    assert response.url == reverse("main")


@pytest.mark.django_db
def test_favorite_redirect_allows_same_host_referer(client, user, planet):
    client.login(username="testuser", password="testpass")
    url = reverse("add_favorite", args=["planet", planet.id])
    referer = "http://testserver" + reverse("profile")
    response = client.post(url, HTTP_REFERER=referer)
    assert response.status_code == 302
    assert response.url == referer


@pytest.mark.django_db
def test_profile_remove_favorite_uses_post_form(client, user, planet):
    ct = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)
    client.login(username="testuser", password="testpass")

    response = client.get(reverse("profile"))
    content = response.content.decode()
    remove_url = reverse("remove_favorite", args=["planet", planet.id])

    assert f'action="{remove_url}"' in content
    assert 'method="post"' in content
    assert "csrfmiddlewaretoken" in content


@pytest.mark.django_db
def test_history_saved_on_planet_detail(client, user, planet):
    client.login(username="testuser", password="testpass")
    url = reverse("planet_detail", args=[planet.id])
    response = client.get(url)
    assert response.status_code == 200
    ct = ContentType.objects.get_for_model(Planet)
    assert History.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()


@pytest.mark.django_db
def test_history_does_not_duplicate(client, user, planet):
    client.login(username="testuser", password="testpass")
    url = reverse("planet_detail", args=[planet.id])
    client.get(url)
    client.get(url)
    ct = ContentType.objects.get_for_model(Planet)
    count = History.objects.filter(user=user, content_type=ct, object_id=planet.id).count()
    assert count == 1
