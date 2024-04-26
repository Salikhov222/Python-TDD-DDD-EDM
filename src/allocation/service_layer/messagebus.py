# Шина сообщений
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential
from typing import TYPE_CHECKING, Dict, Type, List, Callable, Union
from src.allocation.domain import events, commands

if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)
Message = Union[commands.Command, events.Event]     # message - команда либо событие

class AbstractMessageBus(ABC):
    """
    Абстрактная шина сообщений для реализации реальной и фейковой версии
    """
    def __init__(
            self,
            uow: unit_of_work.AbstractUnitOfWork,
            event_handlers: Dict[Type[events.Event], List[Callable]],
            command_handlers: Dict[Type[commands.Command], Callable]
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    @abstractmethod
    def handle(self, message: Message):
        raise NotImplementedError

    @abstractmethod
    def handle_event(self, event: events.Event):
        raise NotImplementedError

    @abstractmethod
    def handle_command(self, command: commands.Command):
        raise NotImplementedError



class MessageBus(AbstractMessageBus):
    """
    Реальная шина сообщений
    """
    
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable]
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        results = []        # временно: ссылка на размещенную партию
        self.queue = [message]     # очередь сообщений
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message)
                results.append(cmd_result)
            else:
                raise Exception(f'{message} was not an Event or Command')
        
        return results

    def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                for attempt in Retrying(        # повторение операций до 3 раз с экспоненциально увеличивающимся ожиданием между попытками
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug('handling event %s with handler %s', event, handler)
                        handler(event)
                        self.queue.extend(self.uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error('Не получилось обработать событие %s %s раз, отказ!', event, retry_failure.last_attempt.attempt_number)
                continue
    
    def handle_command(self, command: commands.Command):
        logger.debug('handling command %s', command)
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            self.queue.extend(self.uow.collect_new_events())
            return result
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise

