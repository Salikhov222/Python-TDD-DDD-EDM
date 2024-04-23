from typing import Optional
from datetime import date
from dataclasses import dataclass

class Command:      # родительский класс команд
    pass

@dataclass
class Allocate(Command):    # команда размещения заказа
    orderid: str
    sku: str
    qty: int

@dataclass
class Deallocate(Command):    # команда отмены размещения заказа
    orderid: str
    sku: str
    qty: int

@dataclass
class CreateBatch(Command):     # команда создания партии
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None

@dataclass
class ChangeBatchQuantity(Command):     # команда изменения размера партии
    ref: str
    qty: int

    