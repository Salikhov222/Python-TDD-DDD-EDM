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
class BatchCreated(Event):      # событие добавления партии товара
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None

@dataclass
class AllocationRequired(Event):     # событие размещения заказа в партии
    orderid: str
    sku: str
    qty: int

@dataclass
class DeallocationRequired(Event):  # событие отмены размещения заказа в партии
    orderid: str
    sku: str
    qty: int

@dataclass
class BatchQuantityChanged(Event):      # событие изменения размера партии
    ref: str
    qty: str