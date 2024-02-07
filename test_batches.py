from datetime import date
from models import OrderLine, Batch


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch("batch-001", sku, batch_qty, eta=date.today()),
        OrderLine('order-123', sku, line_qty)
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    """
    Тест для проверки размещения товарной позиции в партии
    """
    batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=date.today())
    line = OrderLine('order-ref', "SMALL-TABLE", 2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    """
    Тест для проверки размещения позиции в партии, если количество товара в партии > количества товара в позиции
    """
    large_batch, small_line = make_batch_and_line("ELEGANT-LAMP", 20, 2)

    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_smaller_than_required():
    """
    Тест для проверки размещения позиции в партии, если количество товара в партии Б количества товара в позиции
    """
    large_batch, small_line = make_batch_and_line("ELEGANT-LAMP", 2, 20)

    assert large_batch.can_allocate(small_line) is False


def test_can_allocate_if_available_equal_to_required():
    """
    Тест для проверки размещения позиции в партии, если количество товара в партии = количества товара в позиции
    """
    large_batch, small_line = make_batch_and_line("ELEGANT-LAMP", 20, 20)

    assert large_batch.can_allocate(small_line)


def test_can_only_deallocate_allocated_lines():
    """
    Тест для проверки отмены размещения товарной позиции в партии
    """
    batch, unallocated_line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
    batch.deallocate(unallocated_line)

    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    """
    Тест для проверки неизменения количества товара в партии при повторном размещении позиции
    """
    batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18

