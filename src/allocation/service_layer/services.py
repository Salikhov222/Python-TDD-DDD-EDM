from typing import Optional, ContextManager

from datetime import date
from src.allocation import domain
from src.allocation.domain.models import OrderLine, Batch
from src.allocation.adapters.repository import AbstractRepositoriy
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.service_layer import unit_of_work


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


 
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], start_uow: ContextManager[unit_of_work.AbstractUnitOfWork]) -> None:
    """
    Служба сервисного слоя для пополнения товарных запасов партии
    """
    with start_uow as uow:
        uow.batches.add(Batch(ref, sku, qty, eta))
        uow.commit()    


def allocate(orderid: str, sku: str, qty: int, start_uow: ContextManager[unit_of_work.AbstractUnitOfWork]) -> str:
    """
    Служба сервисного слоя для размещения товарной позиции в партии
    """
    line = OrderLine(orderid, sku, qty)
    with start_uow as uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = domain.models.allocate(line, batches)       # вызов службы предметной области
        uow.commit()
    return batchref
    

def deallocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Служба сервисного слоя для отмены размещения товарной позиции в партии
    """    
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):  
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = domain.models.deallocate(line, batches)
        uow.commit()
    return batchref