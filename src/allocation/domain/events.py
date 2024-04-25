from typing import Optional
from datetime import date
from dataclasses import dataclass

# Общий родительский класс для различных событий
class Event:
    pass

@dataclass
class OutOfStock(Event):    # событие отсутствия товара
    sku: str

@dataclass
class Allocated(Event):     # событие о размещение товарной позиции в определенной партии
    orderid: str
    sku: str
    qty: int
    batchref: str

@dataclass
class Deallocated(Event):     # событие отмены размещения товарной позиции
    orderid: str
    sku: str
    qty: int
