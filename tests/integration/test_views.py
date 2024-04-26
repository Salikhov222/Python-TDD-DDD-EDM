import pytest
from datetime import date
from sqlalchemy.orm import clear_mappers
from src.allocation.service_layer import unit_of_work
from src.allocation.domain import commands
from src.allocation import views, bootstrap

today = date.today()

@pytest.fixture
def sqlite_bus(sqlite_session_factory):
    bus = bootstrap.bootstrap(
        start_orm=True,
        uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
        notifications=lambda *args: None,
        publish=lambda *args: None
    )
    yield bus
    clear_mappers()

class TestAllocationsView:

    def test_allocations_view(self, sqlite_bus):
        """Тест для проверки правильного чтения данных размещенных заказов"""

        sqlite_bus.handle(commands.CreateBatch('sku1batch', 'sku1', 20, None))
        sqlite_bus.handle(commands.CreateBatch('sku2batch', 'sku2', 20, today))
        sqlite_bus.handle(commands.Allocate('order1', 'sku1', 20))
        sqlite_bus.handle(commands.Allocate('order1', 'sku2', 20))
        # fake order and batch
        sqlite_bus.handle(commands.CreateBatch('sku1batch-later', 'sku1', 50, today))
        sqlite_bus.handle(commands.Allocate('otherorder', 'sku1', 30))
        sqlite_bus.handle(commands.Allocate('otherorder', 'sku2', 10))

        assert views.allocations('order1', sqlite_bus.uow) == [
            {'sku': 'sku1', 'batchref': 'sku1batch'},
            {'sku': 'sku2', 'batchref': 'sku2batch'}
        ]

    def test_deallocatin_view(self, sqlite_bus):
        """Тест для проверки правильного чтения данных отмененных заказов"""
        sqlite_bus.handle(commands.CreateBatch('sku1batch', 'sku1', 20, None))
        sqlite_bus.handle(commands.CreateBatch('sku2batch', 'sku2', 20, today))
        sqlite_bus.handle(commands.Allocate('order1', 'sku1', 20))
        sqlite_bus.handle(commands.Allocate('order1', 'sku2', 20))

        sqlite_bus.handle(commands.Deallocate('order1', 'sku1', 20))

        assert views.allocations('order1', sqlite_bus.uow) == [
            {'sku': 'sku2', 'batchref': 'sku2batch'}
        ]