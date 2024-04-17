# Шина сообщений
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Type, List, Callable
from src.allocation.domain import events
from . import handlers

if TYPE_CHECKING:
    from . import unit_of_work

class AbstractMessageBus:
    """
    Абстрактная шина сообщений для реализации реальной и фейковой версии
    """
    HANDLERS: Dict[Type[events.Event], List[Callable]]
    
    def handle(self, event: events.Event):
        for handler in self.HANDLERS[type(event)]:
            handler(event)


class MessageBus(AbstractMessageBus):
    """
    Реальная шина сообщений
    """
    HANDLERS = {
        events.OutOfStock: [handlers.send_out_of_stock_notification],
        events.BatchCreated: [handlers.add_batch],
        events.AllocationRequired: [handlers.allocate],
        events.DeallocationRequired: [handlers.deallocate],
        events.BatchQuantityChanged: [handlers.change_batch_quantity]
    }   # тип: Dict[Type[events.Event], List[Callable]]

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        result = []     # временно: ссылка на размещенную партию
        queue = [event]     # очередь событий
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                result.append(handler(event, uow=uow))
                queue.extend(uow.collect_new_events())  # сборка новых событий и добавление в очередь
        
        return result
