import threading
import time
import traceback
import pytest

from sqlalchemy.sql import text
from src.allocation.domain import models
from src.allocation.service_layer import unit_of_work
from src.allocation.adapters import orm
from tests.random_refs import random_batchref, random_orderid, random_sku

def insert_batch(session, ref, sku, qty, eta, product_version=1):
    session.execute(text(
        'INSERT INTO products (sku, version_number)'
        ' VALUES (:sku, :version)').bindparams(sku=sku, version=product_version)
    )
    
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

# Моделирование "медленной" транзации с помощью time.sleep()
def try_to_allocate(orderid, sku, exceptions):
    line = models.OrderLine(orderid, sku, 10)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        with uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)

class TestUoW:

    def test_uow_can_retrieve_a_batch_and_allocate_to_it(self, postgres_session_factory):
        """
        Тест для проверки работы паттерна UoW:
        Создаем и добавляем партию в БД
        Получаем экземпляр этой партии через объект UoW
        Размещаем заказ в партии
        Проверяем, что созданная партия и партия, в которой разместили заказ, идентичны
        """
        session = postgres_session_factory()
        insert_batch(session, 'batch1', "HIPSTER-WORKBENCH", 100, None, product_version=1)
        session.commit()

        uow = unit_of_work.SqlAlchemyUnitOfWork(postgres_session_factory)
        with uow:
            product = uow.products.get(sku='HIPSTER-WORKBENCH')
            line = models.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
            product.allocate(line)
            uow.commit()

        batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
        assert batchref == 'batch1'


    def test_rolls_back_uncomitted_work_by_default(self, sqlite_session_factory):
        """
        Тест для проверки функции rollback при выходе из блока with без вызова метода commit
        """
        uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
        with uow:
            insert_batch(uow.session, 'batch1', 'MEDIUM-PLINTH', 100, None, product_version=1)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute(text('SELECT * FROM "batches"')))
        assert rows == []


    def test_rolls_back_on_error(self, sqlite_session_factory):
        class MyException(Exception):
            pass

        uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
        with pytest.raises(MyException):
            with uow:
                insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None, product_version=1)
                raise MyException()

        new_session = sqlite_session_factory()
        rows = list(new_session.execute(text('SELECT * FROM "batches"')))
        assert rows == []


    def test_concurrent_updates_to_version_are_not_allowed(self, postgres_session_factory):
        """
        Интеграционный тест на параллельное поведение:
        1) Создание партии со случайным артикулом и версией продукта = 1
        2) Генерация двух случайных id заказа
        3) Для каждого заказа запускается функция try_to_allocate в отдельных потоках
        4) Проверка, что версия продукта изменилась один раз и возникло исключение
        5) Проверка на количество записей в таблице allocations: 1 запись - ОК 
        """
        sku, batch = random_sku(), random_batchref()
        session = postgres_session_factory()
        insert_batch(session, batch, sku, 100, eta=None, product_version=1)
        session.commit()

        order1, order2 = random_orderid(1), random_orderid(2)
        exceptions = []     # тип: List[Exception]
        try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
        try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)

        thread1 = threading.Thread(target=try_to_allocate_order1)
        thread2 = threading.Thread(target=try_to_allocate_order2)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        [[version]] = session.execute(text(
            'SELECT version_number FROM products WHERE sku=:sku').bindparams(sku=sku))
        assert version == 2
        [exception] = exceptions
        assert 'could not serialize access due to concurrent update' in str(exception)

        orders = list(session.execute(text(
            'SELECT orderid FROM allocations'
            ' JOIN batches ON allocations.batch_id = batches.id'
            ' JOIN order_lines ON allocations.orderline_id = order_lines.id'
            ' WHERE order_lines.sku=:sku'
        ).bindparams(sku=sku)))
        assert len(orders) == 1
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        with uow:
            uow.session.execute(text('select 1'))