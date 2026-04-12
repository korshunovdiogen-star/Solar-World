import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from users.models import Profile, Favorite, History
from planets.models import Planet

# ---- Фикстуры ----
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
        planet_type="terrestrial",
        text="Марс — четвёртая планета.\nИнтересный факт: ..."
    )

# ---- Тесты регистрации ----
@pytest.mark.django_db
def test_register_view_get(client):
    url = reverse('register')
    response = client.get(url)
    assert response.status_code == 200
    assert 'form' in response.context

@pytest.mark.django_db
def test_register_view_post_success(client):
    url = reverse('register')
    data = {
        'username': 'newuser',
        'password1': 'complex_password_123',
        'password2': 'complex_password_123'
    }
    response = client.post(url, data)
    # Должен быть редирект на главную
    assert response.status_code == 302
    assert response.url == reverse('main')
    # Проверяем, что пользователь создан
    assert User.objects.filter(username='newuser').exists()
    # Проверяем, что профиль создан автоматически (сигнал)
    new_user = User.objects.get(username='newuser')
    assert Profile.objects.filter(user=new_user).exists()

@pytest.mark.django_db
def test_register_view_post_invalid(client):
    url = reverse('register')
    data = {
        'username': 'newuser',
        'password1': 'pass',
        'password2': 'different'
    }
    response = client.post(url, data)
    assert response.status_code == 200  # форма с ошибками
    assert 'form' in response.context
    assert response.context['form'].errors
    assert not User.objects.filter(username='newuser').exists()

# ---- Тесты входа/выхода (Django предоставляет стандартные представления) ----
@pytest.mark.django_db
def test_login_view(client, user):
    url = reverse('login')
    data = {'username': 'testuser', 'password': 'testpass'}
    response = client.post(url, data)
    assert response.status_code == 302
    # Если LOGIN_REDIRECT_URL = 'profile', то редирект на /profile/
    assert response.url == reverse('profile')  # замените на reverse('main') если нужно

@pytest.mark.django_db
def test_logout_view(client, user):
    client.login(username='testuser', password='testpass')
    url = reverse('logout')
    # В современных версиях Django logout работает только через POST
    response = client.post(url)
    assert response.status_code == 302
    # Обычно после выхода редирект на главную
    assert response.url == reverse('main')

# ---- Тесты профиля ----
@pytest.mark.django_db
def test_profile_view_requires_login(client):
    url = reverse('profile')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith('/accounts/login/')

@pytest.mark.django_db
def test_profile_view_authenticated(client, user):
    client.login(username='testuser', password='testpass')
    url = reverse('profile')
    response = client.get(url)
    assert response.status_code == 200
    assert 'user' in response.context
    assert response.context['user'] == user

# ---- Тесты избранного (toggle_favorite) ----
@pytest.mark.django_db
def test_toggle_favorite_add(client, user, planet):
    client.login(username='testuser', password='testpass')
    url = reverse('toggle_favorite')
    data = {'content_type': 'planet', 'object_id': planet.id}
    response = client.post(url, json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp['is_favorite'] is True
    ct = ContentType.objects.get_for_model(Planet)
    assert Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()

@pytest.mark.django_db
def test_toggle_favorite_remove(client, user, planet):
    ct = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)
    client.login(username='testuser', password='testpass')
    url = reverse('toggle_favorite')
    data = {'content_type': 'planet', 'object_id': planet.id}
    response = client.post(url, json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp['is_favorite'] is False
    assert not Favorite.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()

@pytest.mark.django_db
def test_toggle_favorite_unauthenticated(client, planet):
    url = reverse('toggle_favorite')
    data = {'content_type': 'planet', 'object_id': planet.id}
    response = client.post(url, json.dumps(data), content_type='application/json')
    assert response.status_code == 302  # редирект на login

# ---- Тесты истории (автоматическое сохранение при просмотре) ----
@pytest.mark.django_db
def test_history_saved_on_planet_detail(client, user, planet):
    client.login(username='testuser', password='testpass')
    url = reverse('planet_detail', args=[planet.id])
    response = client.get(url)
    assert response.status_code == 200
    ct = ContentType.objects.get_for_model(Planet)
    assert History.objects.filter(user=user, content_type=ct, object_id=planet.id).exists()

# ---- Дополнительно: проверка, что история не дублируется при повторном просмотре ----
@pytest.mark.django_db
def test_history_does_not_duplicate(client, user, planet):
    client.login(username='testuser', password='testpass')
    url = reverse('planet_detail', args=[planet.id])
    client.get(url)
    client.get(url)
    ct = ContentType.objects.get_for_model(Planet)
    count = History.objects.filter(user=user, content_type=ct, object_id=planet.id).count()
    assert count == 1