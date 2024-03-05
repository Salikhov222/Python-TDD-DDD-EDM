from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.api_models import APIAllocateModel, APIDeallocateModel

import config
import domain.models
import service_layer.services
import adapters.orm
import adapters.repository

adapters.orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()

@app.post("/allocate")
async def allocate_endpoint(body: APIAllocateModel):
    """
    Простая реализация конечной точки для размещения заказа в партии товара
    """
    session = get_session() # Создание экземпляра сеанса БД
    repo = adapters.repository.SqlAlchemyRepository(session)     # создание нескольких объектов репозитория
    line = domain.models.OrderLine(        # извлечение из веб-запроса данные пользователя
        body.orderid,
        body.sku,
        body.qty,
    )
    try:
        batchref = service_layer.services.allocate(line, repo, session)       # передача данных в службу предметной области
    except (domain.models.OutOfStock, service_layer.services.InvalidSku) as e:
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
    repo = adapters.repository.SqlAlchemyRepository(session)
    line = domain.models.OrderLine(
        body.orderid,
        body.sku,
        body.qty,
    )
    try:
        batchref = service_layer.services.deallocate(line, repo, session)
    except (domain.models.NoOrderInBatch, service_layer.services.InvalidSku) as e:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return {
        'batchref': batchref
    }