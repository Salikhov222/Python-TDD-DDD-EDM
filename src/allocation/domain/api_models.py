from pydantic import BaseModel
 
 
class OrderLine(BaseModel):
    orderid: str
    sku: str
    qty: int


class APIAllocateModel(OrderLine):
    pass


class APIDeallocateModel(OrderLine):
    pass