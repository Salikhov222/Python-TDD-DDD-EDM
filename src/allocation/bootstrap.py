import inspect
from typing import Callable
from src.allocation.service_layer import unit_of_work, messagebus, handlers
from src.allocation.adapters import redis_eventpublisher, orm, notifications

def bootstrap(
        start_orm: bool = True,
        uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
        notifications: notifications.AbstractNotifications = notifications.EmailNotifications(),
        publish: Callable = redis_eventpublisher.publish
) -> messagebus.MessageBus:
    
    if start_orm:
        orm.start_mappers()     # инициализация при запуске приложения

    dependencies = {'uow': uow, 'notifications': notifications, 'publish': publish}
    injected_event_handlers = {     # создание внедренных версий попарных сопоставлений обработчиков и собыйти/команд
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers
    )

def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters      # проверка аргументов обработчкиа события/команды
    deps = {
        name: dependency
        for name, dependency in dependencies.items()    # соспоставление их по имени с зависимостями загрузчика
        if name in params
    }
    return lambda message: handler(message, **deps)     # внедрение их как именнованные аргументы