from pydantic import BaseModel
from typing import Optional
from datetime import date
 
class APIAllocateModel(BaseModel):
    orderid: str
    sku: str
    qty: int

class  APIAddBatchModel(BaseModel):
    ref: str
    sku: str
    qty: int
    eta: Optional[date]


class APIDeallocateModel(APIAllocateModel):
    pass

