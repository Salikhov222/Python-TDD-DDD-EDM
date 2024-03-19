from abc import ABC, abstractmethod
from src.allocation.domain import models


class AbstractProductRepositoriy(ABC):
    """
     Базовый абстрактный класс-родитель
     add() и get() - два абстрактных метода, которые классы-наследники обязаны реализовать
     Иначе - исключение
    """

    @abstractmethod
    def add(self, product: models.Product):
        raise NotImplementedError
    
    @abstractmethod
    def get(self, sku: str) -> models.Product:
        raise NotImplementedError
    

class SqlAlchemyRepository(AbstractProductRepositoriy):
    """
    Основной класс-репозиторий для работы с приложением
    """

    def __init__(self, session):
        self.session = session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(models.Product).filter_by(sku=sku).first()

