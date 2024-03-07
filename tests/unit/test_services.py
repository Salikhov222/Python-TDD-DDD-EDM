# Тесты, касающиеся оркестровки

from src.allocation.adapters import repository
from src.allocation.service_layer import unit_of_work
import pytest
from src.allocation.domain.models import OrderLine, Batch, NoOrderInBatch
from src.allocation.service_layer import services


class FakeRepository(repository.AbstractRepositoriy):
    """
    Фейковый репозиторий для тестирования приложения
    """

    def __init__(self, batches) -> None:
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
    

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """
    Фейковая реализация UoW для тестирования
    """
    def __init__(self) -> None:
        self.batches = FakeRepository([])
        self.commited = False

    def commit(self) -> None:
        self.commited = True

    def rollback(self) -> None:
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'CRUNCHY-ARMCHAIR', 100, None, uow)
    assert uow.batches.get('b1') is not None
    assert uow.commited


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch('batch1', 'COMPLICATED-LAMP', 100, None, uow)
    result = services.allocate('batch1', 'COMPLICATED-LAMP', 100, uow)
    assert result == 'batch1'


def test_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'COMPLICATED-LAMP', 100, None, uow)

    result = services.allocate('o1', 'COMPLICATED-LAMP', 10, uow)
    assert result == 'b1'

def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'EXIST', 100, None, uow)

    with pytest.raises(services.InvalidSku, match=f'Недопустимый артикул NONE'):
        services.allocate('o1', 'NONE', 10, uow)

def test_commits():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'COMPLICATED-LAMP', 100, None, uow)

    services.allocate('o1', 'COMPLICATED-LAMP', 10, uow)
    assert uow.commited is True

def test_deallocate_decrements_available_quantity():
    """
    Тест для проверки отмены размещения позиции в партии
    """
    uow = FakeUnitOfWork()
    services.add_batch("b1", 'BLUE-PLINTH', 100, None, uow)
    services.allocate('o1', 'BLUE-PLINTH', 10, uow)
    batch = uow.batches.get(reference='b1')
    assert batch.available_quantity == 90
    services.deallocate('o1', 'BLUE-PLINTH', 10, uow)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    ...  #  TODO - check that we decrement the right sku
    uow = FakeUnitOfWork()
    services.add_batch("b1", 'WHITE-TABLE', 100, None, uow)
    ref_batch = services.allocate('o1', 'WHITE-TABLE', 10, uow)
    batch = uow.batches.get(reference='b1')
    assert ref_batch == batch.reference
    services.deallocate('o1', 'WHITE-TABLE', 10, uow)
    assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    ...  #  TODO: should this error or pass silently? up to you.
    uow = FakeUnitOfWork()
    services.add_batch("b1", 'RED-CHAIR', 100, None, uow)
    batch = uow.batches.get(reference='b1')    
    with pytest.raises(NoOrderInBatch, match=f'Товарная позиция RED-CHAIR не размещена ни в одной партии'):
        services.deallocate('o1', 'RED-CHAIR', 10, uow)