from __future__ import annotations
from typing import TYPE_CHECKING
from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.domain import events, commands
from src.allocation.adapters import email, redis_eventpublisher

if TYPE_CHECKING:   # для разрешения конфликта циклического импорта
    from . import unit_of_work    


def add_batch(cmd: commands.CreateBatch, uow: unit_of_work.AbstractUnitOfWork) -> None:
    """
    Обработчик события пополнения товарных запасов партии
    """
    with uow:
        product = uow.products.get(sku=cmd.sku)
        if product is None:
            product = Product(cmd.sku, batches=[])
            uow.products.add(product)
        product.batches.append(Batch(cmd.ref, cmd.sku, cmd.qty, cmd.eta))    
        uow.commit()

def allocate(cmd: commands.Allocate, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Обработчик размещения товарной позиции в партии
    """
    line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.allocate(line)       # вызов службы предметной области
        uow.commit()
        return batchref

# обработчик события отсутствия товара в наличии 
def send_out_of_stock_notification(event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork):
    email.send_mail(
        'stock.@made.com',
        f'Артикула {event.sku} нет в наличии'
    )

def deallocate(cmd: commands.Deallocate, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    Обработчик события отмены размещения товарной позиции в партии
    """    
    line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:     # проверка на правильность введенных данных
            raise InvalidSku(f'Недопустимый артикул {line.sku}')
        batchref = product.deallocate(line)
        uow.commit()
    return batchref

def change_batch_quantity(cmd: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=cmd.ref)
        product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
        uow.commit()

def publish_allocated_event(
        event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork
):
    redis_eventpublisher.publish(event)