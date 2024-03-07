from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.allocation.domain.api_models import APIAllocateModel, APIDeallocateModel, APIAddBatchModel

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
    try:
        batchref = services.allocate(body.orderid, body.sku, body.qty, repo, session)       # передача данных в службу предметной области
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
    try:
        batchref = services.deallocate(body.orderid, body.sku, body.qty, repo, session)
    except (models.NoOrderInBatch, services.InvalidSku) as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {
        'batchref': batchref
    }


@app.post('/batches')
async def add_batch(body: APIAddBatchModel):
    """
    Конечная точка для добавления партии товара
    """
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    eta = body.eta
    try:
        services.add_batch(body.ref, body.sku, body.qty, body.eta, repo, session)
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return {
        'OK'
    }