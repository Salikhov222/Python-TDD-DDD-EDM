from typing import Optional, List

from datetime import date
from dataclasses import dataclass
from src.allocation.domain.exceptions import NoOrderInBatch
from src.allocation.domain import events, commands
from src.allocation.domain.events import Event


@dataclass(unsafe_hash=True)     
class OrderLine:
    """
    Модель данных для хранения данных заказа без какого-либо поведения и изменения
    unsafe_hash = True: Явное определение метода __hash()__, когда класс логически неизменяем,
    но, тем не менее может быть изменен
    """
    orderid: str
    sku: str
    qty: int


class Batch:
    """
    Модель партии товара
    ref - ссылка
    sku - артикул товара
    qty - количество товара
    eta - предполагаемый срок прибытия
    """
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def __eq__(self, other):
        """
        Магический метод, который определяет поведение класса для оператора ==
        """
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        """
        Магический метод, используемый для управления поведением объектов
        при добавлении их в коллекции (set) и в качестве ключей словаря (dict)
        """
        return hash(self.reference)

    def __gt__(self, other):
        """
        Переопределение магического метода для сравнения атрибута eta объектов
        """
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if self.can_deallocate(line):
            self._allocations.remove(line)
    
    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    @property   # позволяет сделать метод вычисляемым свойством
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def can_deallocate(self, line: OrderLine) -> bool:
        return line in self._allocations


class Product:
    events: List[Event] = []    # тип: List[events.Event], события предметной области
    """
    Агрегат, который содержит в себе партии определенного артикула как единое целое
    Для доступа к партиям и к службам предметной области теперь используется Product
    Следовательно во всех абстракциях постоянного хранилища данных (AbstractRepositoriy, FakeRepository, SqlAclhemyRepository, UoW) 
    меняется структура: batches -> products
    """
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0) -> None:
        self.sku = sku      # артикул разных партий, которые представляют себя единым целым - продуктом
        self.batches = batches      # список партий одного артикула
        self.version_number = version_number    # маркер, позволяющий отслеживать изменение версий продукта при параллелизме транзакций
        self.events = []

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            self.events.append(events.Allocated(    # инициализация события для регистрации размещения заказа
                orderid=line.orderid, sku=line.sku, qty=line.qty,
                batchref=batch.reference
            ))
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))     # инициировать OutOfStock(f'Артикула {line.sku} нет в наличии')
            return None 

    def deallocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_deallocate(line))
            batch.deallocate(line)
            self.version_number -= 1
            self.events.append(events.Deallocated(    # инициализация события для регистрации отмены размещения заказа
                orderid=line.orderid, sku=line.sku, qty=line.qty
            ))
            return batch.reference
        except StopIteration:
            raise NoOrderInBatch(f'Товарная позиция {line.sku} не размещена ни в одной партии')

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(
                commands.Allocate(line.orderid, line.sku, line.qty)
            )
