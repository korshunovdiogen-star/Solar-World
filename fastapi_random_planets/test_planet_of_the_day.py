import uuid
from datetime import date

import pytest
from database import DATABASE_URL, Base, get_db
from fastapi.testclient import TestClient
from main import app, get_planet_index
from models import Planet
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def session_factory():
    """Создаёт временную схему PostgreSQL для одного теста."""
    schema = f"fastapi_test_{uuid.uuid4().hex}"
    admin_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute(f'SET search_path TO "{schema}"')
        cursor.close()

    try:
        Base.metadata.create_all(engine)
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()


def make_client(session_factory, planets):
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
def fastapi_client(session_factory):
    client = make_client(
        session_factory,
        [
            Planet(id=5, name="Планета A", order=1, planet_type="TER", radius=1.0),
            Planet(id=10, name="Планета B", order=2, planet_type="TER", radius=2.0),
            Planet(id=20, name="Планета C", order=3, planet_type="TER", radius=3.0),
        ],
    )
    with client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def empty_client(session_factory):
    client = make_client(session_factory, [])
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
