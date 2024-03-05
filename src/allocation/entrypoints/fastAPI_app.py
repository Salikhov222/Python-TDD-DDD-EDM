from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.allocation.domain.api_models import APIAllocateModel, APIDeallocateModel

from src.allocation import config
from src.allocation.domain import models
from src.allocation.service_layer import services
from src.allocation.adapters import orm
from src.allocation.adapters import repository

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()

@app.post("/allocate")
async def allocate_endpoint(body: APIAllocateModel):
    """
    Простая реализация конечной точки для размещения заказа в партии товара
    """
    session = get_session() # Создание экземпляра сеанса БД
    repo = repository.SqlAlchemyRepository(session)     # создание нескольких объектов репозитория
    line = models.OrderLine(        # извлечение из веб-запроса данные пользователя
        body.orderid,
        body.sku,
        body.qty,
    )
    try:
        batchref = services.allocate(line, repo, session)       # передача данных в службу предметной области
    except (models.OutOfStock, services.InvalidSku) as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    
    return {
        'batchref': batchref
    }


@app.post("/deallocate")
async def deallocate_endpoint(body: APIDeallocateModel):
    """
    Конечная точка для отмены размещения позиции в партии
    """
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = models.OrderLine(
        body.orderid,
        body.sku,
        body.qty,
    )
    try:
        batchref = services.deallocate(line, repo, session)
    except (models.NoOrderInBatch, services.InvalidSku) as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {
        'batchref': batchref
    }