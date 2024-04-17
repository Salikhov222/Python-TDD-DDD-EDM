from fastapi import FastAPI, HTTPException, status

from src.allocation.domain.api_models import APIAllocateModel, APIDeallocateModel, APIAddBatchModel
from src.allocation.domain import models, events
from src.allocation.service_layer import unit_of_work, messagebus
from src.allocation.adapters import orm
from src.allocation.domain.exceptions import InvalidSku

orm.start_mappers()
app = FastAPI()

@app.post("/allocate")
async def allocate_endpoint(body: APIAllocateModel):
    """
    Простая реализация конечной точки для размещения заказа в партии товара
    """
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        event = events.AllocationRequired(body.orderid, body.sku, body.qty)       # создание экземпляра события размещения заказа
        result = messagebus.handle(event, uow)      # передача его в шину сообщений
    except InvalidSku as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    
    return {
        'batchref': result.pop(0)
    }


@app.post("/deallocate")
async def deallocate_endpoint(body: APIDeallocateModel):
    """
    Конечная точка для отмены размещения позиции в партии
    """
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        event = events.DeallocationRequired(body.orderid, body.sku, body.qty, uow)
        result = messagebus.handle(event, uow)
    except (models.NoOrderInBatch, InvalidSku) as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {
        'batchref': result.pop(0)
    }


@app.post('/batches')
async def add_batch(body: APIAddBatchModel):
    """
    Конечная точка для добавления партии товара
    """
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        event = events.BatchCreated(body.ref, body.sku, body.qty, body.eta)
        result = messagebus.handle(event, uow)
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return {
        'OK'
    }