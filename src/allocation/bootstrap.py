from typing import Callable
from src.allocation.service_layer import unit_of_work, messagebus, handlers
from src.allocation.adapters import redis_eventpublisher, orm, notifications
from src.allocation.domain import commands, events

def bootstrap(
        start_orm: bool = True,
        uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
        notifications: notifications.AbstractNotifications = notifications.EmailNotifications(),
        publish: Callable = redis_eventpublisher.publish
) -> messagebus.MessageBus:
    
    if start_orm:
        orm.start_mappers()     # инициализация при запуске приложения
        
    injected_event_handlers = {     # создание внедренных версий попарных сопоставлений обработчиков и собыйти/команд
        events.Allocated: [
            handlers.PublishAllocatedEventHandler(publish),
            handlers.AddAllocationToReadModelHandler(uow)
        ],
        events.Deallocated: [
            handlers.RemoveAllocationFromReadModelHandler(uow),
            # handlers.Reallocatehandler(uow)
        ],
        events.OutOfStock: [
            handlers.SendOutOfStockNotificationHandler(notifications)
        ]
    }

    injected_command_handlers = {
        commands.Allocate: handlers.AllocateHandler(uow),
        commands.Deallocate: handlers.DeallocateHandler(uow),
        commands.CreateBatch: handlers.AddBatchHandler(uow),
        commands.ChangeBatchQuantity: handlers.ChangeBatchQuantityHandler(uow)
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers
    )

bus = bootstrap()