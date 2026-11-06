import pytest
from django.contrib.auth.models import User
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse

from users import rate_limit


@pytest.fixture
def rate_cache(monkeypatch):
    """Настоящий кеш вместо DummyCache, чтобы счётчики работали в тестах."""
    cache = LocMemCache("rate-limit-tests", {})
    cache.clear()
    monkeypatch.setattr(rate_limit, "cache", cache)
    return cache


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.mark.django_db
def test_login_is_blocked_after_user_limit(client, user, rate_cache):
    url = reverse("login")

    for _ in range(rate_limit.LOGIN_USER_LIMIT):
        response = client.post(
            url,
            {"username": "testuser", "password": "wrong"},
        )
        assert response.status_code == 200

    response = client.post(
        url,
        {"username": "testuser", "password": "testpass"},
    )

    assert response.status_code == 429
    assert response["Retry-After"] == str(rate_limit.LOGIN_WINDOW_SECONDS)
    assert "Слишком много" in response.content.decode()


@pytest.mark.django_db
def test_correct_password_works_before_limit(client, user, rate_cache):
    url = reverse("login")

    client.post(url, {"username": "testuser", "password": "wrong"})
    response = client.post(
        url,
        {"username": "testuser", "password": "testpass"},
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_first_failure_shows_remaining_attempts(client, user, rate_cache):
    url = reverse("login")

    response = client.post(
        url,
        {"username": "testuser", "password": "wrong"},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Неверный логин или пароль" in content
    assert "Осталось попыток: 4" in content


@pytest.mark.django_db
def test_last_failure_shows_zero_attempts(client, user, rate_cache):
    url = reverse("login")

    for _ in range(rate_limit.LOGIN_USER_LIMIT):
        response = client.post(
            url,
            {"username": "testuser", "password": "wrong"},
        )

    assert "Осталось попыток: 0" in response.content.decode()


def test_login_page_has_no_attempts_message(client, rate_cache):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert "Осталось попыток" not in response.content.decode()


@pytest.mark.django_db
def test_successful_login_resets_failures(client, user, rate_cache):
    url = reverse("login")

    client.post(url, {"username": "testuser", "password": "wrong"})
    assert not rate_limit.is_limited(
        "login-ip-user",
        "127.0.0.1|testuser",
        rate_limit.LOGIN_USER_LIMIT,
    )

    client.post(url, {"username": "testuser", "password": "testpass"})

    assert not rate_limit.is_limited(
        "login-ip-user",
        "127.0.0.1|testuser",
        1,
    )


@pytest.mark.django_db
def test_other_username_is_not_blocked_by_user_limit(client, user, rate_cache):
    url = reverse("login")

    for _ in range(rate_limit.LOGIN_USER_LIMIT):
        client.post(url, {"username": "testuser", "password": "wrong"})

    response = client.post(
        url,
        {"username": "otheruser", "password": "wrong"},
    )

    # Лимит по паре «IP + логин» для другого логина ещё не исчерпан.
    assert response.status_code == 200


@pytest.mark.django_db
def test_ip_limit_blocks_different_usernames(client, rate_cache, monkeypatch):
    # Уменьшаем лимит, чтобы не делать 20 медленных проверок пароля.
    monkeypatch.setattr("users.views.LOGIN_IP_LIMIT", 3)
    url = reverse("login")

    for index in range(3):
        response = client.post(
            url,
            {"username": f"user{index}", "password": "wrong"},
        )
        assert response.status_code == 200

    response = client.post(
        url,
        {"username": "another-user", "password": "wrong"},
    )

    assert response.status_code == 429


def test_client_ip_ignores_forwarded_header_locally(settings, rf):
    settings.TRUST_PROXY_HEADERS = False
    request = rf.post(
        "/accounts/login/",
        REMOTE_ADDR="10.0.0.1",
        HTTP_X_FORWARDED_FOR="1.2.3.4",
    )

    assert rate_limit.get_client_ip(request) == "10.0.0.1"


def test_client_ip_uses_forwarded_header_behind_proxy(settings, rf):
    settings.TRUST_PROXY_HEADERS = True
    request = rf.post(
        "/accounts/login/",
        REMOTE_ADDR="10.0.0.1",
        HTTP_X_FORWARDED_FOR="1.2.3.4, 10.0.0.1",
    )

    assert rate_limit.get_client_ip(request) == "1.2.3.4"


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="adminuser",
        password="adminpass",
        is_staff=True,
    )


@pytest.mark.django_db
def test_admin_login_page_is_available(client, admin_user, rate_cache):
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_login_is_blocked_after_user_limit(client, admin_user, rate_cache):
    url = reverse("admin:login")

    for _ in range(rate_limit.LOGIN_USER_LIMIT):
        response = client.post(
            url,
            {"username": "adminuser", "password": "wrong"},
        )
        assert response.status_code == 200

    response = client.post(
        url,
        {"username": "adminuser", "password": "adminpass"},
    )

    assert response.status_code == 429
    assert response["Retry-After"] == str(rate_limit.LOGIN_WINDOW_SECONDS)
    assert "Слишком много" in response.content.decode()


@pytest.mark.django_db
def test_admin_login_resets_failures_after_success(client, admin_user, rate_cache):
    url = reverse("admin:login")

    client.post(url, {"username": "adminuser", "password": "wrong"})
    response = client.post(
        url,
        {"username": "adminuser", "password": "adminpass"},
    )

    assert response.status_code == 302
    assert not rate_limit.is_limited(
        "login-ip-user",
        "127.0.0.1|adminuser",
        1,
    )


@pytest.mark.django_db
def test_authenticated_user_cannot_reset_admin_login_limit(
    client,
    user,
    admin_user,
    rate_cache,
):
    # Обычный пользователь уже вошёл на сайт и пытается подобрать пароль админа.
    client.force_login(user)
    url = reverse("admin:login")

    for _ in range(rate_limit.LOGIN_USER_LIMIT):
        response = client.post(
            url,
            {"username": "adminuser", "password": "wrong"},
        )
        assert response.status_code == 200

    response = client.post(
        url,
        {"username": "adminuser", "password": "adminpass"},
    )

    assert response.status_code == 429
