class OutOfStock(Exception):    # Исключение могут выражать понятия из предметной области
    """
    Исключение в случае отсутствия товара в наличии
    """
    pass


class NoOrderInBatch(Exception):
    """
    Исключение, в случае отсутствия товарной позиции в партии
    """
    pass


class InvalidSku(Exception):
    pass
