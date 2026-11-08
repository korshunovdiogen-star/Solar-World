from datetime import date

import pytest

from planets.models import Mission, Planet


class FakeCache:
    """Кеш без Redis: запоминает, по каким маскам просили удаление."""

    def __init__(self):
        self.patterns = []

    def delete_pattern(self, pattern):
        self.patterns.append(pattern)


@pytest.fixture
def fake_cache(monkeypatch):
    fake = FakeCache()
    monkeypatch.setattr("planets.signals.cache", fake)
    return fake


def make_planet(name="Марс"):
    return Planet.objects.create(
        name=name,
        order=4,
        radius=3390,
        planet_type="TER",
    )


@pytest.mark.django_db
def test_save_and_delete_invalidate_detail_and_catalog(fake_cache):
    planet = make_planet()
    fake_cache.patterns.clear()

    planet.name = "Марс II"
    planet.save()
    assert set(fake_cache.patterns) == {"*:detail", "*cache_page*"}

    fake_cache.patterns.clear()
    planet.delete()
    assert set(fake_cache.patterns) == {"*:detail", "*cache_page*"}


@pytest.mark.django_db
def test_m2m_change_invalidates_detail_and_catalog(fake_cache):
    planet = make_planet()
    mission = Mission.objects.create(name="Тестовая миссия", launch_date=date(2026, 1, 1))
    fake_cache.patterns.clear()

    mission.target_planets.add(planet)

    assert set(fake_cache.patterns) == {"*:detail", "*cache_page*"}
