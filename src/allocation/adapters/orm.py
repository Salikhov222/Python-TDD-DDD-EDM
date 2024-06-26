from sqlalchemy.orm import registry, relationship
from sqlalchemy import MetaData, Table, Column, Integer, String, Date, ForeignKey
from src.allocation.domain import models

metadata = MetaData()
mapper_reg = registry()     # Замена mapper в версии SQLALchemy 2.0

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('qty', Integer, nullable=False),
    Column('orderid', String(255)),
)

products = Table(
    'products', metadata,
    Column('sku', String(255), primary_key=True),
    Column("version_number", Integer, nullable=False, server_default="0"),
)

batches = Table(
    'batches', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('reference', String(255)),
    Column('sku', ForeignKey('products.sku')),
    Column('_purchased_quantity', Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)

allocations_view = Table(
    'allocations_view', metadata,
    Column('orderid', String(255)),
    Column('sku', String(255)),
    Column('batchref', String(255))
)

def start_mappers():
    lines_mapper = mapper_reg.map_imperatively(models.OrderLine, order_lines)   # Привязка класса модели к таблице
    batches_mapper = mapper_reg.map_imperatively(
        models.Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper, secondary=allocations, collection_class=set
            )
        }
    )
    mapper_reg.map_imperatively(models.Product, products, properties={"batches": relationship(batches_mapper)})