from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation.domain.api_models import APIAllocateModel, APIDeallocateModel, APIAddBatchModel
from src.allocation import config
from src.allocation.domain import models
from src.allocation.service_layer import services, unit_of_work
from src.allocation.adapters import orm
from src.allocation.adapters import repository

orm.start_mappers()
app = FastAPI()

@app.post("/allocate")
async def allocate_endpoint(body: APIAllocateModel):
    """
    Простая реализация конечной точки для размещения заказа в партии товара
    """
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.allocate(body.orderid, body.sku, body.qty, uow)       # передача данных в службу предметной области
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
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.deallocate(body.orderid, body.sku, body.qty, uow)
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
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        services.add_batch(body.ref, body.sku, body.qty, body.eta, uow)
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return {
        'OK'
    }