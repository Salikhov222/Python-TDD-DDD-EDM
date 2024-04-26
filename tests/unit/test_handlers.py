# Тесты, касающиеся оркестровки
from collections import defaultdict
import pytest
from datetime import date
from src.allocation import bootstrap
from src.allocation.adapters import repository, notifications
from src.allocation.service_layer import unit_of_work, messagebus, handlers
from src.allocation.domain import events, commands

class FakeRepository(repository.AbstractProductRepositoriy):
    """
    Фейковый репозиторий для тестирования приложения
    """

    def __init__(self, products) -> None:
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)
    
    def _get_by_batchref(self, batchref):
        return next((p for p in self._products for b in p.batches if b.reference == batchref), None)

    

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """
    Фейковая реализация UoW для тестирования
    """
    def __init__(self) -> None:
        self.products = FakeRepository([])
        self.commited = False

    def _commit(self) -> None:
        self.commited = True

    def rollback(self) -> None:
        pass

def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        notifications=lambda *args: None,
        publish=lambda *args: None
    )

# TODO: довести до ума
class FakeMessageBus(messagebus.AbstractMessageBus):
    """
    Фейковая шина сообщений для изолированного тестирования каждого обработчика событий
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.events_published = []      # тип: List[events.Event]
        self.HANDLERS = {
            events.OutOfStock: [lambda e: self.events_published.append(e)],
        }

class FakeNotifications(notifications.AbstractNotifications):

    def __init__(self) -> None:
        self.sent = defaultdict(list)   # Тип Dict[str, List[str]]

    def send(self, destination, message):
        self.sent[destination].append(message)


class TestAddBatch:

    def test_add_batch_for_new_product(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'CRUNCHY-ARMCHAIR', 100, None))
        [batch] = bus.uow.products.get('CRUNCHY-ARMCHAIR').batches
        assert bus.uow.products.get('CRUNCHY-ARMCHAIR') is not None
        assert bus.uow.commited

    def test_add_batch_for_existing_product(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'CRUNCHY-ARMCHAIR', 100, None))
        bus.handle(commands.CreateBatch('b2', 'CRUNCHY-ARMCHAIR', 99, None))
        assert 'b2' in [b.reference for b in bus.uow.products.get('CRUNCHY-ARMCHAIR').batches]



class TestAllocate:

    def test_returns_allocation(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'COMPLICATED-LAMP', 100, None))

        result = bus.handle(commands.Allocate('o1', 'COMPLICATED-LAMP', 10))
        assert result.pop(0) == 'b1'

    def test_error_for_invalid_sku(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'EXIST', 100, None))

        with pytest.raises(handlers.InvalidSku, match=f'Недопустимый артикул NONE'):
            bus.handle(commands.Allocate('o1', 'NONE', 10))

    def test_commits(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', 'COMPLICATED-LAMP', 100, None))

        bus.handle(commands.Allocate('o1', 'COMPLICATED-LAMP', 10))
        assert bus.uow.commited is True


class TestChangeBatchQuantity:

    def test_changes_available_quantity(self):
        """
        Тест для проверки обработки события изменения размера партии
        """
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('batch1', 'CHAIR2', 100, None))
        [batch] = bus.uow.products.get(sku='CHAIR2').batches 
        assert batch.available_quantity == 100

        bus.handle(commands.ChangeBatchQuantity('batch1', 50))
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        """
        Тест для проверки события изменения размера партии с отменой размещенных заказов в этой партии
        и их повторным размещением 
        """
        bus = bootstrap_test_app()
        event_history = [
            commands.CreateBatch('batch1', 'TABLE', 50, None),
            commands.CreateBatch('batch2', 'TABLE', 50, date.today()),
            commands.Allocate('order1', 'TABLE', 20),
            commands.Allocate('order2', 'TABLE', 20)
        ]

        for e in event_history:
            bus.handle(e)
        [batch1, batch2] = bus.uow.products.get(sku='TABLE').batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        bus.handle(commands.ChangeBatchQuantity('batch1', 25))

        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30

class TestSendNotification:

    def test_sends_email_on_out_of_stock_error(self):
        fake_notifs = FakeNotifications()
        bus = bootstrap.bootstrap(
            start_orm=False,
            uow=FakeUnitOfWork(),
            notifications=fake_notifs,
            publish=lambda *args: None
        )

        bus.handle(commands.CreateBatch('b1', 'POPULAR-CURTAINS', 9, None))
        bus.handle(commands.Allocate('o1', 'POPULAR-CURTAINS', 10))
        assert fake_notifs.sent['stock@made.com'] == [f'Артикула POPULAR-CURTAINS нет в наличии']