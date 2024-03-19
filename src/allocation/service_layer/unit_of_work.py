from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation import config
from src.allocation.adapters import repository


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ",      # уровень изоляции сеанса для соблюдения правил параллелизма
    ))


class AbstractUnitOfWork(ABC):  # Абстрактный контекстный менеджер
    products: repository.AbstractProductRepositoriy     # создание объекта репозитория для доступа партиям

    def __exit__(self, *args):  # магический метод, который выполняется при входе в блок with
        self.rollback()
    
    def __enter__(self):
        pass

    @abstractmethod
    def commit(self):
        raise NotImplementedError
    
    @abstractmethod
    def rollback(self):
        raise NotImplementedError
    

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):     # Реализация абстракции UoW
    
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY) -> None:
        self.session_factory = session_factory

    def __enter__(self):
        """
        Запуск сеанс БД и создание экземпляра реального репозитория
        """
        self.session = self.session_factory() # тип: Session
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    # магический метод, который выполняется при выходе в блок with
    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
