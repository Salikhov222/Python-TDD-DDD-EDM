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


def test_uow_can_retrieve_a_batch_and_allocate_to_it(sqlite_session):
    """
    Тест для проверки работы паттера UoW:
    Создаем и добавляем партию в БД
    Получаем экземпляр этой партии через объект UoW
    Размещаем заказ в партии
    Проверяем, что созданная партия и партия, в которой разместили заказ, идентичны
    """
    session = sqlite_session()
    insert_batch(session, 'batch1', "HIPSTER-WORKBENCH", 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session)
    with uow:
        batch = uow.batches.get(reference='batch1')
        line = models.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'
