from dataclasses import dataclass

# Общий родительский класс для различных событий
class Event:
    pass

@dataclass
class OutOfStock(Event):    # событие отсутствия товара
    sku: str
