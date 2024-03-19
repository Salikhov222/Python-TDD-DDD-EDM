# Тесты, касающиеся оркестровки

from src.allocation.adapters import repository
from src.allocation.service_layer import unit_of_work
import pytest
from src.allocation.domain.models import OrderLine, Batch, NoOrderInBatch
from src.allocation.service_layer import services


class FakeRepository(repository.AbstractProductRepositoriy):
    """
    Фейковый репозиторий для тестирования приложения
    """

    def __init__(self, products) -> None:
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)

    

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """
    Фейковая реализация UoW для тестирования
    """
    def __init__(self) -> None:
        self.products = FakeRepository([])
        self.commited = False

    def commit(self) -> None:
        self.commited = True

    def rollback(self) -> None:
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'CRUNCHY-ARMCHAIR', 100, None, uow)
    assert uow.products.get('CRUNCHY-ARMCHAIR') is not None
    assert uow.commited

def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'CRUNCHY-ARMCHAIR', 100, None, uow)
    services.add_batch('b2', 'CRUNCHY-ARMCHAIR', 99, None, uow)
    assert 'b2' in [b.reference for b in uow.products.get('CRUNCHY-ARMCHAIR').batches]

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

