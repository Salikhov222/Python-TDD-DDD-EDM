from datetime import date, timedelta
from src.allocation.domain.models import OrderLine, Batch, Product
from src.allocation.domain import events


today = date.today()
tomorrow =today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_prefers_current_stock_batches_to_shipments():
    """
    Тест для проверки размещения товарных позиций в складских партиях, а не в партиях с некоторым временем прибытия
    """
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("oref", "RETRO-CLOCK", 10)
    product = Product(sku="RETRO-CLOCK", batches=[in_stock_batch, shipment_batch])

    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100
    

def test_prefers_earlier_batches():
    """
    Тест для проверки правильного выбора приоритета партии к размещению -
    чем раньше срок, тем более партия приоритетна
    """
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
    latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
    line = OrderLine("order1", "MINIMALIST-SPOON", 10)
    product = Product(sku="MINIMALIST-SPOON", batches=[earliest, medium, latest])

    product.allocate(line)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    """
    Тест для проверки эквивалентности ссылки на партию, приоритетной к размещению
    """
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow)
    line = OrderLine("oref", "HIGHBROW-POSTER", 10)
    product = Product(sku="HIGHBROW-POSTER", batches=[in_stock_batch, shipment_batch])

    allocation = product.allocate(line)

    assert allocation == in_stock_batch.reference


def test_records_out_of_stock_exception_if_cannot_allocate():
    """
    Тест для проверки вызова исключения при отсутствии товара в наличии
    """
    batch = Batch('batch1', 'SMALL-FORK', 10, eta=today)
    product = Product(sku='SMALL-FORK', batches=[batch])
    product.allocate(OrderLine('order1', "SMALL-FORK", 10))

    allocation = product.allocate(OrderLine('order2', 'SMALL-FORK', 1))
    assert product.events[-1] == events.OutOfStock(sku='SMALL-FORK')
    assert allocation is None
    