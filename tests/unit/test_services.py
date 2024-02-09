# Тесты, касающиеся оркестровки

import adapters.repository
import pytest
from domain.models import OrderLine, Batch
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