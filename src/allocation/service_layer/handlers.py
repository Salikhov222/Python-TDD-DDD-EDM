from __future__ import annotations
from dataclasses import asdict
from typing import TYPE_CHECKING, Callable
from sqlalchemy.sql import text

from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.domain import events, commands
from src.allocation.adapters import notifications

if TYPE_CHECKING:   # для разрешения конфликта циклического импорта
    from . import unit_of_work    

class AllocateHandler:
    """
    Обработчик размещения товарной позиции в партии
    """

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, cmd: commands.Allocate) -> str:
        line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
        with self.uow:
            product = self.uow.products.get(sku=line.sku)
            if product is None:     # проверка на правильность введенных данных
                raise InvalidSku(f'Недопустимый артикул {line.sku}')
            batchref = product.allocate(line)       # вызов службы предметной области
            self.uow.commit()
            return batchref

class DeallocateHandler:
    """
    Обработчик события отмены размещения товарной позиции в партии
    """    
    
    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, cmd: commands.Deallocate) -> str:
        line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
        with self.uow:
            product = self.uow.products.get(sku=line.sku)
            if product is None:     # проверка на правильность введенных данных
                raise InvalidSku(f'Недопустимый артикул {line.sku}')
            batchref = product.deallocate(line)
            self.uow.commit()
        return batchref

class AddBatchHandler:
    """
    Обработчик события пополнения товарных запасов партии
    """
    
    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, cmd: commands.CreateBatch) -> None:
        with self.uow:
            product = self.uow.products.get(sku=cmd.sku)
            if product is None:
                product = Product(cmd.sku, batches=[])
                self.uow.products.add(product)
            product.batches.append(Batch(cmd.ref, cmd.sku, cmd.qty, cmd.eta))    
            self.uow.commit()

class ChangeBatchQuantityHandler:
    """
    Обработчик события изменения размера партии
    """

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, cmd: commands.ChangeBatchQuantity) -> None:
        with self.uow:
            product = self.uow.products.get_by_batchref(batchref=cmd.ref)
            product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
            self.uow.commit()

class SendOutOfStockNotificationHandler:
    """
    Обработчик события отсутствия товара в наличии
    """

    def __init__(self, notification: notifications.AbstractNotifications) -> None:
        self.notification = notification

    def __call__(self, event: events.OutOfStock) -> None:
        self.notification.send(
            'stock@made.com',
            f'Артикула {event.sku} нет в наличии'
        )
    
class PublishAllocatedEventHandler:
    """
    Обработчик события регистрации размещения заказа для публикации в Redis
    """

    def __init__(self, publish: Callable) -> None:
        self.publish = publish

    def __call__(self, event: events.Allocated) -> None:
        self.publish(event)

class AddAllocationToReadModelHandler:
    """
    Обработчик события регистрации события размещения заказа для обновление модели чтения данных
    """   

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow
    
    def __call__(self, event: events.Allocated) -> None:
        with self.uow:
            self.uow.session.execute(text(
                'INSERT INTO allocations_view (orderid, sku, batchref)'
                ' VALUES (:orderid, :sku, :batchref)'
            ).bindparams(orderid=event.orderid, sku=event.sku, batchref=event.batchref))
            self.uow.commit()

class RemoveAllocationFromReadModelHandler:
    """
    Обработичк события отмены размещения заказа для обновления модели чтения данных
    """

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, event: events.Deallocated) -> None:
        with self.uow:
            self.uow.session.execute(text(
                'DELETE FROM allocations_view WHERE orderid = :orderid AND sku = :sku'
            ).bindparams(orderid=event.orderid, sku=event.sku))
            self.uow.commit()

class Reallocatehandler:
    """
    Обработчик события отмены размещения заказа для его повторного размещения
    """

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork) -> None:
        self.uow = uow

    def __call__(self, event: events.Deallocated) -> None:
        with self.uow:
            product = self.uow.products.get(sku=event.sku)
            product.events.append(commands.Allocate(**asdict(event)))
            self.uow.commit()