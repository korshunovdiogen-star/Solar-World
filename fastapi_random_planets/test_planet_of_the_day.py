from datetime import date

import pytest
from database import Base, get_db
from fastapi.testclient import TestClient
from main import app, get_planet_index
from models import Planet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_client(planets):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    session = session_factory()
    session.add_all(planets)
    session.commit()
    session.close()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def fastapi_client():
    client = make_client(
        [
            Planet(id=5, name="Планета A", order=1, planet_type="TER", radius=1.0),
            Planet(id=10, name="Планета B", order=2, planet_type="TER", radius=2.0),
            Planet(id=20, name="Планета C", order=3, planet_type="TER", radius=3.0),
        ]
    )
    with client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def empty_client():
    client = make_client([])
    with client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize("total_count", [1, 2, 3, 8, 20])
def test_index_always_fits_planet_count(total_count):
    index = get_planet_index(date(2026, 11, 4), total_count)

    assert 0 <= index < total_count


def test_index_is_stable_for_same_date():
    first = get_planet_index(date(2026, 11, 4), 8)
    second = get_planet_index(date(2026, 11, 4), 8)

    assert first == second


def test_planet_of_the_day_returns_existing_id(fastapi_client):
    response = fastapi_client.get("/planet/today")

    assert response.status_code == 200
    assert response.json()["planet_id"] in {5, 10, 20}


def test_empty_database_returns_404(empty_client):
    response = empty_client.get("/planet/today")

    assert response.status_code == 404
