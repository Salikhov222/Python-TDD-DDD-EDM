from abc import ABC, abstractmethod


class AbstractNotifications(ABC):
    """
    Абстрактная реализация API уведомлений
    """
    @abstractmethod
    def send(self, message):
        raise NotImplementedError

class EmailNotifications(AbstractNotifications):
    """
    Реализация фейковой отправки уведомления
    """
    def send(self, message):
        print(f'Subject: allocation service notification\n{message}')