from __future__ import annotations
from dataclasses import asdict
from typing import TYPE_CHECKING
from sqlalchemy.sql import text

from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.domain import events, commands
from src.allocation.adapters import notifications, redis_eventpublisher

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

def send_out_of_stock_notification(event: events.OutOfStock, notifications: notifications.AbstractNotifications):
    """
    Обработчик события отсутствия товара в наличии
    """
    notifications.send(
        'stock@made.com',
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
    """
    Обработчик события изменения размера партии
    """
    with uow:
        product = uow.products.get_by_batchref(batchref=cmd.ref)
        product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
        uow.commit()

def publish_allocated_event(
        event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork
):
    """
    Обработчик события регистрации размещения заказа для публикации в Redis
    """
    redis_eventpublisher.publish(event)

def add_allocation_to_read_model(
        event: events.Allocated, uow: unit_of_work.SqlAlchemyUnitOfWork
):
    """
    Обработчик события регистрации события размещения заказа для обновление модели чтения данных
    """
    with uow:
        uow.session.execute(text(
            'INSERT INTO allocations_view (orderid, sku, batchref)'
            ' VALUES (:orderid, :sku, :batchref)'
        ).bindparams(orderid=event.orderid, sku=event.sku, batchref=event.batchref))
        uow.commit()

def remove_allocation_from_read_model(
        event: events.Deallocated, uow: unit_of_work.SqlAlchemyUnitOfWork
):
    """
    Обработичк события отмены размещения заказа для обновления модели чтения данных
    """
    with uow:
        uow.session.execute(text(
            'DELETE FROM allocations_view WHERE orderid = :orderid AND sku = :sku'
        ).bindparams(orderid=event.orderid, sku=event.sku))
        uow.commit()

def reallocate(
        event: events.Deallocated, uow: unit_of_work.SqlAlchemyUnitOfWork
):
    """
    Обработчик события отмены размещения заказа для его повторного размещения
    """
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(**asdict(event)))
        uow.commit()

EVENT_HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.Allocated: [publish_allocated_event, add_allocation_to_read_model],
    events.Deallocated: [remove_allocation_from_read_model]
}   # тип: Dict[Type[events.Event], List[Callable]]

COMMAND_HANDLERS = {
    commands.CreateBatch: add_batch,
    commands.Allocate: allocate,
    commands.Deallocate: deallocate,
    commands.ChangeBatchQuantity: change_batch_quantity
}   # тип: Dict[Type[commands.Command], Callable]