# Тесты, касающиеся оркестровки

from src.allocation.adapters import repository
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
    
class FakeSession():
    """
    Временный фейковый сеанс БД, для указания фиксации данных в БД
    """
    commited = False

    def commit(self):
        self.commited = True


def test_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch('b1', 'COMPLICATED-LAMP', 100, None, repo, session)

    result = services.allocate('o1', 'COMPLICATED-LAMP', 10, repo, FakeSession())
    assert result == 'b1'

def test_error_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch('b1', 'EXIST', 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match=f'Недопустимый артикул NONE'):
        services.allocate('o1', 'NONE', 10, repo, session)

def test_commits():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch('b1', 'COMPLICATED-LAMP', 100, None, repo, session)

    services.allocate('o1', 'COMPLICATED-LAMP', 10, repo, session)
    assert session.commited is True

def test_deallocate_decrements_available_quantity():
    """
    Тест для проверки отмены размещения позиции в партии
    """
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", 'BLUE-PLINTH', 100, None, repo, session)
    services.allocate('o1', 'BLUE-PLINTH', 10, repo, session)
    batch = repo.get(reference='b1')
    assert batch.available_quantity == 90
    services.deallocate('o1', 'BLUE-PLINTH', 10, repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    ...  #  TODO - check that we decrement the right sku
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", 'WHITE-TABLE', 100, None, repo, session)
    ref_batch = services.allocate('o1', 'WHITE-TABLE', 10, repo, session)
    batch = repo.get(reference='b1')
    assert ref_batch == batch.reference
    services.deallocate('o1', 'WHITE-TABLE', 10, repo, session)
    assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    ...  #  TODO: should this error or pass silently? up to you.
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", 'RED-CHAIR', 100, None, repo, session)
    batch = repo.get(reference='b1')    
    with pytest.raises(NoOrderInBatch, match=f'Товарная позиция RED-CHAIR не размещена ни в одной партии'):
        services.deallocate('o1', 'RED-CHAIR', 10, repo, session)