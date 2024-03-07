from src.allocation.domain import models
from sqlalchemy.sql import text


def test_orderline_mapper_can_load_lines(sqlite_session):
    sqlite_session.execute(text(
        'INSERT INTO order_lines (orderid, sku, qty) VALUES '
        '("order1", "RED-CHAIR", 12),'
        '("order2", "RED-TABLE", 13),'
        '("order3", "RED-LIPSTICK", 14)')
    )
    expected = [
        models.OrderLine("order1", "RED-CHAIR", 12),
        models.OrderLine("order2", "RED-TABLE", 13),
        models.OrderLine("order3", "RED-LIPSTICK", 14)
    ]

    assert sqlite_session.query(models.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(sqlite_session):
    new_line = models.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    sqlite_session.add(new_line)
    sqlite_session.commit()

    rows = list(sqlite_session.execute(text('SELECT orderid, sku, qty FROM order_lines')))

    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]



