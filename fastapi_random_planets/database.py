import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent

# FastAPI запускается из папки fastapi_random_planets, а .env лежит в корне.
load_dotenv(BASE_DIR / ".env")

# Демо-база лежит в demo_data/ — тот же файл, что использует Django
# при работе без PostgreSQL. Путь должен совпадать с settings.SQLITE_DB_PATH.
SQLITE_URL = f"sqlite:///{BASE_DIR / 'demo_data' / 'db.sqlite3'}"


def _database_url():
    """Возвращает адрес базы: DATABASE_URL или PostgreSQL из DB_*, иначе SQLite."""
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url:
        return url

    engine = (os.getenv("DB_ENGINE") or "").strip().lower()
    if not engine.endswith("postgresql"):
        return SQLITE_URL

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "solar_bd")

    return (
        f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}" f"@{host}:{port}/{name}"
    )


DATABASE_URL = _database_url()

# check_same_thread нужен только SQLite: FastAPI работает с базой в разных потоках.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
