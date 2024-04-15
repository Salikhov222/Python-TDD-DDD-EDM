from abc import ABC, abstractmethod
from src.allocation.domain import models


class AbstractProductRepositoriy(ABC):
    """
     Базовый абстрактный класс-родитель
     add() и get() - два абстрактных метода, которые классы-наследники обязаны реализовать
     Иначе - исключение
    """

    def __init__(self) -> None:
        self.seen = set()   # type: set[models.Product]

    def add(self, product: models.Product):
        self._add(product)
        self.seen.add(product)
    
    def get(self, sku) -> models.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abstractmethod
    def _add(self, product: models.Product):
        raise NotImplementedError
    
    @abstractmethod
    def _get(self, sku: str) -> models.Product:
        raise NotImplementedError
    

class SqlAlchemyRepository(AbstractProductRepositoriy):
    """
    Основной класс-репозиторий для работы с приложением
    """

    def __init__(self, session):
        super.__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(models.Product).filter_by(sku=sku).first()

