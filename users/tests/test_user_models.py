import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from users.models import Profile, Favorite, History
from planets.models import Planet, Satellite  # для создания тестовых объектов

# Фикстура для пользователя
@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass")

# Фикстура для планеты (как пример объекта, который можно добавить в избранное/историю)
@pytest.fixture
def planet():
    return Planet.objects.create(name="Марс", order=4, radius=3390, planet_type="terrestrial")

# --- Тесты для Profile ---
@pytest.mark.django_db
def test_profile_created_with_user(user):
    """Профиль должен создаваться автоматически при создании пользователя (сигнал)"""
    profile = Profile.objects.get(user=user)
    assert profile.user == user
    assert str(profile) == f"Профиль пользователя {user.username}"

# --- Тесты для Favorite ---
@pytest.mark.django_db
def test_favorite_creation(user, planet):
    ct = ContentType.objects.get_for_model(Planet)
    favorite = Favorite.objects.create(
        user=user,
        content_type=ct,
        object_id=planet.id
    )
    assert favorite.user == user
    assert favorite.content_object == planet
    assert str(favorite) == f"{user.username} -> {planet}"

@pytest.mark.django_db
def test_favorite_unique_constraint(user, planet):
    """Один пользователь не может добавить один и тот же объект дважды"""
    ct = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)
    with pytest.raises(Exception):  # IntegrityError
        Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)

@pytest.mark.django_db
def test_favorite_related_name(user, planet):
    """Проверка обратной связи: user.favorites"""
    ct = ContentType.objects.get_for_model(Planet)
    Favorite.objects.create(user=user, content_type=ct, object_id=planet.id)
    assert user.favorites.count() == 1
    assert user.favorites.first().content_object == planet

# --- Тесты для History ---
@pytest.mark.django_db
def test_history_creation(user, planet):
    ct = ContentType.objects.get_for_model(Planet)
    history = History.objects.create(
        user=user,
        content_type=ct,
        object_id=planet.id
    )
    assert history.user == user
    assert history.content_object == planet
    assert history.viewed_at is not None
    assert str(history) == f"{user.username} -> {planet} ({history.viewed_at})"

@pytest.mark.django_db
def test_history_unique_together(user, planet):
    """Один пользователь не может иметь две записи об одном объекте (unique_together)"""
    ct = ContentType.objects.get_for_model(Planet)
    History.objects.create(user=user, content_type=ct, object_id=planet.id)
    # Повторное создание должно обновить viewed_at (update_or_create), но если просто create, то ошибка
    # Проверяем, что unique_together настроен
    with pytest.raises(Exception):
        History.objects.create(user=user, content_type=ct, object_id=planet.id)

@pytest.mark.django_db
def test_history_ordering(user, planet):
    """Записи истории должны сортироваться по убыванию viewed_at"""
    ct = ContentType.objects.get_for_model(Planet)
    h1 = History.objects.create(user=user, content_type=ct, object_id=planet.id)
    # Создадим второй объект (спутник)
    satellite = Satellite.objects.create(name="Фобос", radius=11, planet=planet)
    ct2 = ContentType.objects.get_for_model(Satellite)
    h2 = History.objects.create(user=user, content_type=ct2, object_id=satellite.id)
    # Получаем историю пользователя
    history_list = History.objects.filter(user=user)
    # По умолчанию order by -viewed_at
    assert history_list[0] == h2  # более поздний (новый) должен быть первым
    assert history_list[1] == h1