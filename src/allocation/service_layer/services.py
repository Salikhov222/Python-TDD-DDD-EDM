from typing import Optional

from datetime import date
from src.allocation import domain
from src.allocation.domain.models import OrderLine, Batch
from src.allocation.adapters.repository import AbstractRepositoriy
from src.allocation.domain.exceptions import InvalidSku


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepositoriy, session) -> str:
    """
    Служба сервисного слоя для размещения товарной позиции в партии
    """
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):     # проверка на правильность введенных данных
        raise InvalidSku(f'Недопустимый артикул {line.sku}')
    batchref = domain.models.allocate(line, batches)       # вызов службы предметной области
    session.commit()
    return batchref
    
 
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepositoriy, session) -> None:
    """
    Служба сервисного слоя для пополнения товарных запасов партии
    """
    repo.add(Batch(ref, sku, qty, eta))    
    session.commit()


def deallocate(orderid: str, sku: str, qty: int, repo: AbstractRepositoriy, session) -> str:
    """
    Служба сервисного слоя для отмены размещения товарной позиции в партии
    """    
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):  
        raise InvalidSku(f'Недопустимый артикул {line.sku}')
    batchref = domain.models.deallocate(line, batches)
    session.commit()
    return batchref