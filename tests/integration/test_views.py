from datetime import date
from src.allocation.service_layer import messagebus
from src.allocation.service_layer import unit_of_work
from src.allocation.domain import commands
from src.allocation import views

today = date.today()

class TestAllocationsView:

    def test_allocations_view(self, sqlite_session_factory):
        """Тест для проверки правильного чтения данных размещенных заказов"""

        uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
        msgBus = messagebus.MessageBus()
        msgBus.handle(commands.CreateBatch('sku1batch', 'sku1', 20, None), uow)
        msgBus.handle(commands.CreateBatch('sku2batch', 'sku2', 20, today), uow)
        msgBus.handle(commands.Allocate('order1', 'sku1', 20), uow)
        msgBus.handle(commands.Allocate('order1', 'sku2', 20), uow)
        # fake order and batch
        msgBus.handle(commands.CreateBatch('sku1batch-later', 'sku1', 50, today), uow)
        msgBus.handle(commands.Allocate('otherorder', 'sku1', 30), uow)
        msgBus.handle(commands.Allocate('otherorder', 'sku2', 10), uow)

        assert views.allocations('order1', uow) == [
            {'sku': 'sku1', 'batchref': 'sku1batch'},
            {'sku': 'sku2', 'batchref': 'sku2batch'}
        ]

    def test_deallocatin_view(self, sqlite_session_factory):
        """Тест для проверки правильного чтения данных отмененных заказов"""
        uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
        msgBus = messagebus.MessageBus()
        msgBus.handle(commands.CreateBatch('sku1batch', 'sku1', 20, None), uow)
        msgBus.handle(commands.CreateBatch('sku2batch', 'sku2', 20, today), uow)
        msgBus.handle(commands.Allocate('order1', 'sku1', 20), uow)
        msgBus.handle(commands.Allocate('order1', 'sku2', 20), uow)

        msgBus.handle(commands.Deallocate('order1', 'sku1', 20), uow)

        assert views.allocations('order1', uow) == [
            {'sku': 'sku2', 'batchref': 'sku2batch'}
        ]