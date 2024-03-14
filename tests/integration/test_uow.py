import pytest
from sqlalchemy.sql import text
from src.allocation.domain import models
from src.allocation.service_layer import unit_of_work


def insert_batch(session, ref, sku, qty, eta):
    session.execute(text(
        'INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)').bindparams(ref=ref, sku=sku, qty=qty, eta=eta)
    )

def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(text(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku').bindparams(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(text(
        'SELECT b.reference FROM allocations JOIN batches as b ON batch_id = b.id'
        ' WHERE orderline_id=:orderlineid',
    ).bindparams(orderlineid=orderlineid))

    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(sqlite_session_factory):
    """
    Тест для проверки работы паттера UoW:
    Создаем и добавляем партию в БД
    Получаем экземпляр этой партии через объект UoW
    Размещаем заказ в партии
    Проверяем, что созданная партия и партия, в которой разместили заказ, идентичны
    """
    session = sqlite_session_factory()
    insert_batch(session, 'batch1', "HIPSTER-WORKBENCH", 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        batch = uow.batches.get(reference='batch1')
        line = models.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'


def test_rolls_back_uncomitted_work_by_default(sqlite_session_factory):
    """
    Тест для проверки функции rollback при выходе из блока with без вызова метода commit
    """
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        insert_batch(uow.session, 'batch1', 'MEDIUM-PLINTH', 100, None)

    new_session = sqlite_session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "batches"')))
    assert rows == []


def test_rolls_back_on_error(sqlite_session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None)
            raise MyException()

    new_session = sqlite_session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "batches"')))
    assert rows == []