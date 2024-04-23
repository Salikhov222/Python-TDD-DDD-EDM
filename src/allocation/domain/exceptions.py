class NoOrderInBatch(Exception):
    """
    Исключение, в случае отсутствия товарной позиции в партии
    """
    pass


class InvalidSku(Exception):
    pass
