# Шина сообщений

from src.allocation.adapters import email
from src.allocation.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)

# обработчик события отсутствия товара в наличии 
def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
        'stock.@made.com',
        f'Артикула {event.sku} нет в наличии'
    )

HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}   # тип: Dict[Type[events.Event], List[Callable]]

