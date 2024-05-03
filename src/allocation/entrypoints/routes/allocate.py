from typing import Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.encoders import jsonable_encoder

from src.allocation.domain.api_models import PostAllocateModel, PostDeallocateModel, GetAllocationsModel
from src.allocation.domain import commands, models
from src.allocation.domain.exceptions import InvalidSku
from src.allocation.bootstrap import bus
from src.allocation import views

allocate_router = APIRouter(tags=["Allocate"])

@allocate_router.post("/")
async def allocate_endpoint(body: PostAllocateModel) -> Dict:
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
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={'batchref': result.pop(0)}
    )

@allocate_router.delete("/")
async def deallocate_endpoint(body: PostDeallocateModel) -> Dict:
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
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={'batchref': result.pop(0)}
    )

@allocate_router.get("/{orderid}", response_model=GetAllocationsModel)
async def allocations_view_endpoint(orderid) -> Dict:
    """
    Конечная точка для просмотра размещенных заказов модели данных для чтения
    """
    result = views.allocations(orderid, bus.uow)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)