from typing import Optional

from datetime import date
import domain.models
from domain.models import OrderLine, Batch
from adapters.repository import AbstractRepositoriy


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepositoriy, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):     # проверка на правильность введенных данных
        raise InvalidSku(f'Недопустимый артикул {line.sku}')
    batchref = domain.models.allocate(line, batches)       # вызов службы предметной области
    session.commit()
    return batchref
    
 
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepositoriy, session) -> None:
    batch = Batch(ref, sku, qty, eta)
    repo.add(batch)    
    session.commit()


def deallocate(line: OrderLine, repo: AbstractRepositoriy, session) -> str:    
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):  
        raise InvalidSku(f'Недопустимый артикул {line.sku}')
    batchref = domain.models.deallocate(line, batches)
    session.commit()
    return batchref