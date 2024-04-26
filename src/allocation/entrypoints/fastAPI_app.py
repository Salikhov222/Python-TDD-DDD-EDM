import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from src.allocation.domain.api_models import PostAddBatchModel, PostAllocateModel, PostDeallocateModel, GetAllocationsModel
from src.allocation.domain import models, commands
from src.allocation.domain.exceptions import InvalidSku
from src.allocation import bootstrap, views

app = FastAPI()
bus = bootstrap.bootstrap()

@app.post("/allocate")
async def allocate_endpoint(body: PostAllocateModel):
    """
    Простая реализация конечной точки для размещения заказа в партии товара
    """
    try:
        command = commands.Allocate(body.orderid, body.sku, body.qty)       # создание экземпляра события размещения заказа
        result = bus.handle(command)      # передача его cценарий начальной загрузки
    except InvalidSku as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    
    return {
        'batchref': result.pop(0)
    }


@app.post("/deallocate")
async def deallocate_endpoint(body: PostDeallocateModel):
    """
    Конечная точка для отмены размещения позиции в партии
    """
    try:
        command = commands.Deallocate(body.orderid, body.sku, body.qty)
        result = bus.handle(command)
    except (models.NoOrderInBatch, InvalidSku) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {
        'batchref': result.pop(0)
    }


@app.post('/batches')
async def add_batch(body: PostAddBatchModel):
    """
    Конечная точка для добавления партии товара
    """
    try:
        command = commands.CreateBatch(body.ref, body.sku, body.qty, body.eta)
        result = bus.handle(command)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content={})


@app.get('/allocations/{orderid}', response_model=GetAllocationsModel)
async def allocations_view_endpoint(orderid):
    """
    Конечная точка для просмотра размещенных заказов модели данных для чтения
    """
    result = views.allocations(orderid, bus.uow)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)