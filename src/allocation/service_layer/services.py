from typing import Optional

from datetime import date
from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain.exceptions import InvalidSku
from . import messagebus, unit_of_work


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], uow: unit_of_work.AbstractUnitOfWork) -> None:
    """
    Служба сервисного слоя для пополнения товарных запасов партии
    """
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(Batch(ref, sku, qty, eta))    
        uow.commit()

def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Служба сервисного слоя для размещения товарной позиции в партии
    """
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.allocate(line)       # вызов службы предметной области
        uow.commit()
        return batchref

def deallocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Служба сервисного слоя для отмены размещения товарной позиции в партии
    """    
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.deallocate(line)
        uow.commit()
    return batchref