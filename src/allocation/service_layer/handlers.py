from __future__ import annotations
from typing import TYPE_CHECKING
from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.domain import events
from src.allocation.adapters import email

if TYPE_CHECKING:   # для разрешения конфликта циклического импорта
    from . import unit_of_work    


def add_batch(event: events.BatchCreated, uow: unit_of_work.AbstractUnitOfWork) -> None:
    """
    Обработчик события пополнения товарных запасов партии
    """
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(Batch(event.ref, event.sku, event.qty, event.eta))    
        uow.commit()

def allocate(event: events.AllocationRequired, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Обработчик размещения товарной позиции в партии
    """
    line = OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.allocate(line)       # вызов службы предметной области
        uow.commit()
        return batchref

# обработчик события отсутствия товара в наличии 
def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
        'stock.@made.com',
        f'Артикула {event.sku} нет в наличии'
    )

def deallocate(event: events.DeallocationRequired, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Обработчик события отмены размещения товарной позиции в партии
    """    
    line = OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.deallocate(line)
        uow.commit()
    return batchref

def change_batch_quantity(event: events.BatchQuantityChanged, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
