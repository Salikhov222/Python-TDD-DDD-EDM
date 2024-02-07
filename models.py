from typing import Optional, List

from datetime import date
from dataclasses import dataclass


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
        if line in self._allocations:
            self._allocations.remove(line)

    @property   # позволяет сделать метод вычисляемым свойством
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity


class OutOfStock(Exception):    # Исключение могут выражать понятия из предметной области
    """
    Исключение в случае отсутствия товара в наличии
    """
    pass


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """
    Автономная функция для службы предментой области, а именно
    для службы размещения товарных позиций в конкретном наборе партий
    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f'Артикула {line.sku} нет в наличии')

