import pytest
from django.urls import reverse
from planets.models import Planet, Satellite, Mission, SpaceAgency, Company

@pytest.mark.django_db
def test_planet_creation():
    planet = Planet.objects.create(
        name="Марс",
        radius=3390,
        planet_type="terrestrial",
        order=4,
    )
    assert planet.name == "Марс"
    assert planet.radius == 3390
    assert str(planet) == "Марс"

@pytest.mark.django_db
@pytest.mark.parametrize("name, radius, ptype, order", [
    ("Меркурий", 2440, "terrestrial", 1),
    ("Юпитер", 69911, "gas_giant", 2),
    ("Плутон", 1188, "dwarf", 3),
])
def test_planet_types(name, radius, ptype, order):
    planet = Planet.objects.create(name=name, radius=radius, planet_type=ptype, order=order)
    assert planet.planet_type == ptype


@pytest.mark.django_db
def test_satellite_creation():
    # Сначала создадим планету-хозяина
    planet = Planet.objects.create(name="Марс", radius=3390, order=4)
    satellite = Satellite.objects.create(
        name="Фобос",
        radius=11,
        satellite_type="irregular",   # тип спутника (регулярный/нерегулярный)
        planet=planet
    )
    assert satellite.name == "Фобос"
    assert satellite.radius == 11
    assert satellite.planet.name == "Марс"
    assert str(satellite) == "Фобос"

@pytest.mark.django_db
@pytest.mark.parametrize("name, radius, sat_type", [
    ("Луна", 1737, "regular"),
    ("Деймос", 6, "irregular"),
    ("Европа", 1561, "regular"),
])
def test_satellite_types(name, radius, sat_type):
    # Для параметризации нужна планета-хозяин
    planet = Planet.objects.create(name="Тестовая планета", radius=99999, order=99)
    satellite = Satellite.objects.create(
        name=name,
        radius=radius,
        satellite_type=sat_type,
        planet=planet
    )
    assert satellite.satellite_type == sat_type

# --- Тесты для Mission ---
@pytest.mark.django_db
def test_mission_creation():
    mission = Mission.objects.create(
        name="Аполлон-11",
        mission_type="piloted",
        launch_date="1969-07-16",
        status="completed",
        success=True
    )
    assert mission.name == "Аполлон-11"
    assert mission.success is True
    assert str(mission) == "Аполлон-11"

@pytest.mark.django_db
@pytest.mark.parametrize("name, mtype, success", [
    ("Вояджер-1", "flyby", True),
    ("Марс-3", "lander", False),
    ("JWST", "telescope", True),
])
def test_mission_types(name, mtype, success):
    mission = Mission.objects.create(
        name=name,
        mission_type=mtype,
        launch_date="2000-01-01",
        status="completed" if success else "failed",
        success=success
    )
    assert mission.mission_type == mtype
    assert mission.success == success

# --- Тесты для SpaceAgency ---
@pytest.mark.django_db
def test_agency_creation():
    agency = SpaceAgency.objects.create(
        name="NASA",
        country="США",
        established_date="1958-07-29"
    )
    assert agency.name == "NASA"
    assert agency.country == "США"
    assert str(agency) == "NASA"

# --- Тесты для Company ---
@pytest.mark.django_db
def test_company_creation():
    company = Company.objects.create(
        name="SpaceX",
        country="США",
        established_date="2002-03-14",
        founders="Илон Маск",
        employees=13000,
        CEO="Илон Маск",
        revenue_2025=15500.00
    )
    assert company.name == "SpaceX"
    assert company.country == "США"
    assert company.employees == 13000
    assert str(company) == "SpaceX"




@pytest.mark.django_db
def test_planet_detail_view(client):
    planet = Planet.objects.create(
        name="Марс",
        radius=3390,
        planet_type="terrestrial",
        order=4,
        text="Марс — четвёртая планета.\nИнтересный факт: ..."
    )
    url = reverse('planet_detail', args=[planet.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Марс" in response.content.decode()

@pytest.mark.django_db
def test_satellite_detail_view(client):
    planet = Planet.objects.create(name="Марс", radius=999999, order=4)
    satellite = Satellite.objects.create(
        name="Фобос",
        radius=11,
        satellite_type="irregular",
        planet=planet,
        text="Фобос — спутник Марса.\nОписание..."
    )
    url = reverse('satellite_detail', args=[satellite.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Фобос" in response.content.decode()

@pytest.mark.django_db
def test_mission_detail_view(client):
    mission = Mission.objects.create(
        name="Аполлон-11",
        mission_type="piloted",
        launch_date="1969-07-16",
        status="completed",
        success=True,
        text="Первая высадка на Луну.\nОписание..."
    )
    url = reverse('mission_detail', args=[mission.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Аполлон-11" in response.content.decode()

@pytest.mark.django_db
def test_spaceagency_detail_view(client):
    agency = SpaceAgency.objects.create(
        name="NASA",
        country="США",
        established_date="1958-07-29",
        text="Национальное управление по аэронавтике и исследованию космического пространства.\nОписание..."
    )
    url = reverse('spaceagency_detail', args=[agency.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "NASA" in response.content.decode()

@pytest.mark.django_db
def test_company_detail_view(client):
    company = Company.objects.create(
        name="SpaceX",
        country="США",
        established_date="2002-03-14",
        founders="Илон Маск",
        employees=13000,
        CEO="Илон Маск",
        revenue_2025=15500.00,
        text="Компания, основанная Илоном Маском.\nОписание..."
    )
    url = reverse('company_detail', args=[company.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "SpaceX" in response.content.decode()

@pytest.mark.django_db
def test_planet_list_view(client):
    mars = Planet.objects.create(name="Марс", order=4, radius=3390, planet_type="terrestrial")
    venus = Planet.objects.create(name="Венера", order=2, radius=6052, planet_type="terrestrial")
    url = reverse('planet_list')
    response = client.get(url)
    assert response.status_code == 200
    assert mars in response.context['planets']
    assert venus in response.context['planets'] 