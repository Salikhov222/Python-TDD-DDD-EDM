from abc import ABC, abstractmethod
import domain.models


class AbstractRepositoriy(ABC):
    """
     Базовый абстрактный класс-родитель
     add() и get() - два абстрактных метода, которые классы-наследники обязаны реализовать
     Иначе - исключение
    """

    @abstractmethod
    def add(self, batch: domain.models.Batch):
        raise NotImplementedError
    
    @abstractmethod
    def get(self, reference) -> domain.models.Batch:
        raise NotImplementedError
    

class SqlAlchemyRepository(AbstractRepositoriy):
    """
    Основной класс-репозиторий для работы с приложением
    """

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(domain.models.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(domain.models.Batch).all()
