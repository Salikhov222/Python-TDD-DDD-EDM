# Тесты, касающиеся оркестровки

import adapters.repository
import pytest
from domain.models import OrderLine, Batch, NoOrderInBatch
import service_layer.services


class FakeRepository(adapters.repository.AbstractRepositoriy):
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
    
class FakeSession():
    """
    Временный фейковый сеанс БД, для указания фиксации данных в БД
    """
    commited = False

    def commit(self):
        self.commited = True


def test_returns_allocation():
    line = OrderLine('o1', 'COMPLICATED-LAMP', 10)
    batch = Batch('b1', 'COMPLICATED-LAMP', 100, eta=None)
    repo = FakeRepository([batch])

    result = service_layer.services.allocate(line, repo, FakeSession())
    assert result == 'b1'

def test_error_for_invalid_sku():
    line = OrderLine('o1', 'NONE', 10)
    batch = Batch('b1', 'EXIST', 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(service_layer.services.InvalidSku, match=f'Недопустимый артикул {line.sku}'):
        service_layer.services.allocate(line, repo, FakeSession())

def test_commits():
    line = OrderLine('o1', 'COMPLICATED-LAMP', 10)
    batch = Batch('b1', 'COMPLICATED-LAMP', 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    service_layer.services.allocate(line, repo, session)
    assert session.commited is True

def test_deallocate_decrements_available_quantity():
    """
    Тест для проверки отмены размещения позиции в партии
    """
    repo, session = FakeRepository([]), FakeSession()
    service_layer.services.add_batch("b1", 'BLUE-PLINTH', 100, None, repo, session)
    line = OrderLine('o1', 'BLUE-PLINTH', 10)
    service_layer.services.allocate(line, repo, session)
    batch = repo.get(reference='b1')
    assert batch.available_quantity == 90
    service_layer.services.deallocate(line, repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    ...  #  TODO - check that we decrement the right sku
    repo, session = FakeRepository([]), FakeSession()
    service_layer.services.add_batch("b1", 'WHITE-TABLE', 100, None, repo, session)
    line = OrderLine('o1', 'WHITE-TABLE', 10)
    ref_batch = service_layer.services.allocate(line, repo, session)
    batch = repo.get(reference='b1')
    assert ref_batch == batch.reference
    service_layer.services.deallocate(line, repo, session)
    assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    ...  #  TODO: should this error or pass silently? up to you.
    repo, session = FakeRepository([]), FakeSession()
    service_layer.services.add_batch("b1", 'RED-CHAIR', 100, None, repo, session)
    batch = repo.get(reference='b1')    
    line = OrderLine('o1', 'RED-CHAIR', 10)
    with pytest.raises(NoOrderInBatch, match=f'Товарная позиция {line.sku} не размещена ни в одной партии'):
        service_layer.services.deallocate(line, repo, session)