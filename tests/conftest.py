import time
import pytest
from src.allocation import config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.exc import OperationalError
from src.allocation.adapters.orm import metadata, start_mappers


# Создание движка БД и таблиц
@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine

# Привязка моделей к таблицам, создание сессии БД и очистка таблиц
@pytest.fixture
def sqlite_session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()

@pytest.fixture
def sqlite_session(sqlite_session_factory):
    return sqlite_session_factory()

# Проверка работы службы PostgreSQL сервера
def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")

# Создание БД postgres
@pytest.fixture(scope='session')
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine

# Привязка моделей к таблицам, создание сессии БД postgres и очистка таблиц
@pytest.fixture
def postgres_session_factory(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)
    clear_mappers()

@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()
