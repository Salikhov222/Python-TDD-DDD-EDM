# Шина сообщений
from __future__ import annotations
import logging
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential
from typing import TYPE_CHECKING, Dict, Type, List, Callable, Union
from src.allocation.domain import events, commands
from . import handlers

if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)
Message = Union[commands.Command, events.Event]     # message - команда либо событие

class AbstractMessageBus:
    """
    Абстрактная шина сообщений для реализации реальной и фейковой версии
    """
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[commands.Command], Callable]

    def handle_event(self, event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                handler(event, uow=uow)
                queue.extend(uow.collect_new_events())
            except Exception:
                continue

    def handle_command(self, command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
            try:
                for handler in self.COMMAND_HANDLERS[type(command)]:
                    handler(command, uow=uow)
                    queue.extend(uow.collect_new_events())
            except Exception:
                raise

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        for handler in self.HANDLERS[type(event)]:
            handler(event, uow)


class MessageBus(AbstractMessageBus):
    """
    Реальная шина сообщений
    """
    EVENT_HANDLERS = {
        events.OutOfStock: [handlers.send_out_of_stock_notification],
        events.Allocated: [handlers.publish_allocated_event]
    }   # тип: Dict[Type[events.Event], List[Callable]]

    COMMAND_HANDLERS = {
        commands.CreateBatch: handlers.add_batch,
        commands.Allocate: handlers.allocate,
        commands.Deallocate: handlers.deallocate,
        commands.ChangeBatchQuantity: handlers.change_batch_quantity
    }   # тип: Dict[Type[commands.Command], Callable]

    def handle(self, message: Message, uow: unit_of_work.AbstractUnitOfWork):
        results = []        # временно: ссылка на размещенную партию
        queue = [message]     # очередь сообщений
        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message, queue, uow)
                results.append(cmd_result)
            else:
                raise Exception(f'{message} was not an Event or Command')
        
        return results

    def handle_event(
            self,
            event: events.Event,
            queue: List[Message],
            uow: unit_of_work.AbstractUnitOfWork
    ):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                for attempt in Retrying(        # повторение операций до 3 раз с экспоненциально увеличивающимся ожиданием между попытками
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug('handling event %s with handler %s', event, handler)
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error('Не получилось обработать событие %s %s раз, отказ!', event, retry_failure.last_attempt.attempt_number)
                continue
    
    def handle_command(
            self,
            command: commands.Command,
            queue: List[Message],
            uow: unit_of_work.AbstractUnitOfWork
    ):
        logger.debug('handling command %s', command)
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise

