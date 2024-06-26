from abc import ABC, abstractmethod
from sqlalchemy import select
from src.allocation.domain import models
from src.allocation.adapters import orm


class AbstractProductRepositoriy(ABC):
    """
     Базовый абстрактный класс-родитель
     add() и get() - два абстрактных метода, которые классы-наследники обязаны реализовать
     Иначе - исключение
    """

    def __init__(self) -> None:
        self.seen = set()   # атрибут, отслеживающий агрегаты, type: set[models.Product]

    def add(self, product: models.Product):
        self._add(product)
        self.seen.add(product)
    
    def get(self, sku) -> models.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product
    
    def get_by_batchref(self, batchref) -> models.Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abstractmethod
    def _add(self, product: models.Product):
        raise NotImplementedError
    
    @abstractmethod
    def _get(self, sku: str) -> models.Product:
        raise NotImplementedError
    
    @abstractmethod
    def _get_by_batchref(self, batchref: str) -> models.Product:
        raise NotImplementedError
    

class SqlAlchemyRepository(AbstractProductRepositoriy):
    """
    Основной класс-репозиторий для работы с приложением
    """

    def __init__(self, session):
        super().__init__()      # для инициализации множества seen
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(models.Product).filter_by(sku=sku).first()
    
    def _get_by_batchref(self, batchref):   # поиск продукта по ссылке партии
        return self.session.query(models.Product).join(models.Batch).filter(orm.batches.c.reference == batchref).first()

