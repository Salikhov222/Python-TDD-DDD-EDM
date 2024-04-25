from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date
 
class PostAllocateModel(BaseModel):
    orderid: str
    sku: str
    qty: int

class PostAddBatchModel(BaseModel):
    ref: str
    sku: str
    qty: int
    eta: Optional[date]

class PostDeallocateModel(PostAllocateModel):
    pass

class GetAllocationsModel(BaseModel):
    allocations: List[Dict[str, str]]