from typing import ContextManager
from contextlib import contextmanager

from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.allocation import config
from src.allocation.adapters import repository


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.get_postgres_uri()))

# Декоратор contextmanager возвращает объект с автоматически созданными методами __enter__() и __exit__()
@contextmanager
def start_uow(session_factory=DEFAULT_SESSION_FACTORY):
    session = session_factory()

    try:
        uow = SqlAlchemyUnitOfWork(session)
        yield uow
    except:
        session.rollback()
        raise
    finally:
        session.close()

class AbstractUnitOfWork(ABC):

    abstractmethod
    def commit(self):
        raise NotImplementedError

    abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self.batches = repository.SqlAlchemyRepository(session)
    
    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
