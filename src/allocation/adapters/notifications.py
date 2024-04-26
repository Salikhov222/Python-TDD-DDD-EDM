from abc import ABC, abstractmethod
import smtplib
from src.allocation import config


class AbstractNotifications(ABC):
    """
    Абстрактная реализация API уведомлений
    """
    @abstractmethod
    def send(self, destination, message):
        raise NotImplementedError
    
DEFAULT_HOST = config.get_email_host_and_port()["host"]
DEFAULT_PORT = config.get_email_host_and_port()["port"]

class EmailNotifications(AbstractNotifications):
    """
    Реализация отправки уведомлений через email
    """
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT) -> None:
        self.server = smtplib.SMTP(smtp_host, port=port)
        self.server.noop()

    def send(self, destination, message):
        msg = f'Subject: allocation service notofication\n{message}'
        self.server.sendmail(
            from_addr='allocations@example.com',
            to_addrs=[destination],
            msg=msg
        )
        