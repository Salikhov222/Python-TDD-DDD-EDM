import pytest
import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.sql import text
from adapters.orm import metadata, start_mappers


# Создание движка БД и таблиц
@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


# Привязка моделей к таблицам, создание сессии БД и очистка таблиц
@pytest.fixture
def sqlite_session(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


# Создание БД postgres
@pytest.fixture(scope='session')
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    metadata.create_all(engine)
    return engine


# Привязка моделей к таблицам, создание сессии БД postgres и очистка таблиц
@pytest.fixture
def postgres_session(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


# Добавление данных в БД с помощью SQL для тестирования и удаление после тестов
@pytest.fixture
def add_stock(postgres_session):
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        """
        Добавление партий товаров в БД
        """
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                text("INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                     " VALUES (:ref, :sku, :qty, :eta)").bindparams(ref=ref, sku=sku, qty=qty, eta=eta)
            )
            [[batch_id]] = postgres_session.execute(
                text("SELECT id FROM batches WHERE reference=:ref AND sku=:sku").bindparams(ref=ref, sku=sku)
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    # Очистка БД от данных, используемых в тестировании
    for batch_id in batches_added:
        postgres_session.execute(
            text('DELETE FROM allocations WHERE batch_id=:batch_id').bindparams(batch_id=batch_id)
        )
        postgres_session.execute(
            text('DELETE FROM batches WHERE id=:batch_id').bindparams(batch_id=batch_id)
        )

    for sku in skus_added:
        postgres_session.execute(
            text('DELETE FROM order_lines WHERE sku=:sku').bindparams(sku=sku)
        )
        postgres_session.commit()
