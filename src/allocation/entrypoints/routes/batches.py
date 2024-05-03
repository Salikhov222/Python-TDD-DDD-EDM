from typing import Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.encoders import jsonable_encoder

from src.allocation.domain.api_models import PostAddBatchModel
from src.allocation.domain import commands
from src.allocation.bootstrap import bus


batches_router = APIRouter(tags=["Batches"])

@batches_router.post('/')
async def add_batch(body: PostAddBatchModel) -> Dict:
    """
    Конечная точка для добавления партии товара
    """
    try:
        command = commands.CreateBatch(body.ref, body.sku, body.qty, body.eta)
        bus.handle(command)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder({"Batch added"}))