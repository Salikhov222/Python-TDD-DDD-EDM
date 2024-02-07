import models
import repository
from conftests import session, in_memory_db
from sqlalchemy.sql import text


def insert_order_line(session) -> str:  # создание товарнцой позиции
    session.execute(
        text('INSERT INTO order_lines (orderid, sku, qty)'
             ' VALUES ("order1", "GENERIC-SOFA", 12)')
    )

    [[orderline_id]] = session.execute(
        text('SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku').bindparams(orderid="order1", sku="GENERIC-SOFA"),
    )

    return orderline_id

def insert_batch(session, batch_id) -> str:     # создание партии товара
    session.execute(
        text('INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
             ' VALUES (:batch_id, "GENERIC-SOFA", 100, Null)').bindparams(batch_id=batch_id)
    )

    [[batch_id]] = session.execute(
        text('SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"').bindparams(batch_id=batch_id),
    )

    return batch_id


def insert_allocation(session, orderline_id, batch_id) -> None:     # размещение заказа в партии
    session.execute(
        text('INSERT INTO allocations (orderline_id, batch_id)' 
             ' VALUES (:orderline_id, :batch_id)').bindparams(orderline_id=orderline_id, batch_id=batch_id),
    )


def get_allocations(session, batch_id) -> str:
    rows = list(
        session.execute(
            text('SELECT orderid FROM allocations JOIN order_lines ON allocations.orderline_id = order_lines.id'
                 ' JOIN batches ON allocations.batch_id = batches.id WHERE batches.reference = :batch_id').bindparams(batch_id=batch_id),
        )
    )
    return {row[0] for row in rows}


def test_repository_can_save_a_batch(session):
    """
    Тест репозитория на сохранение объекта
    """
    batch = models.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
    
    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = list(session.execute(text('SELECT reference, sku, _purchased_quantity, eta FROM "batches"')))

    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]



def test_repository_can_retrieve_a_batch_with_allocations(session):
    """
    Тест на извлечение сложного объекта:
    1) Создается заказ
    2) Создаются 2 разные партии товара
    3) Размещается заказ в определенной партии
    4) Сравниваются типы, ссылка и атрибуты партии
    """
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, 'batch1')
    insert_batch(session, 'batch2')
    insert_allocation(session, orderline_id, batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get('batch1')

    expected = models.Batch('batch1', 'GENERIC-SOFA', 100, eta=None)
    assert retrieved == expected    # Batch.__eq__ сравнивает только ссылку
    
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        models.OrderLine('order1', 'GENERIC-SOFA', 12)
    }


def test_updating_a_batch(session):
    """
    Тест репозитория на обновление партии товара при повтороном размещении заказа
    """
    order1 = models.OrderLine("order1", 'TABLE', 10)
    order2 = models.OrderLine("order2", 'TABLE', 20)
    batch = models.Batch('batch1', 'TABLE', 100, eta=None)    
    batch.allocate(order1)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    batch.allocate(order2)
    repo.add(batch)
    session.commit()

    assert get_allocations(session, 'batch1') == {'order1', 'order2'}



