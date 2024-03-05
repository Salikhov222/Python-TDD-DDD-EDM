# Сквозные тесты Е2Е для всего, что связано с вебом

import pytest
import config
import requests
import uuid


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"


def test_happy_path_returns_200_and_allocated_batch(add_stock):
    """
    Первый сквозной тест для проверки использования конечной точки API 
    и связывания с реальной БД
    """
    # random_sku(), random_batchref - вспомогательные функции для генерации строки для артикула и ссылки
    # используются как один из способов предотвратить влияние различных тестов и запусков друг на друга при работа с реальной БД
    sku, othersku = random_sku(), random_sku('other')
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    # add_stock() вспомогательный инструмент, которая просто скрывает детали ручной вставки строк в БД с помощью SQL
    add_stock([
        (laterbatch, sku, 100, '2011-01-02'),
        (earlybatch, sku, 100, '2011-01-01'),
        (otherbatch, othersku, 100, None),
    ])
    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    
    assert r.status_code == 200
    assert r.json()['batchref'] == earlybatch
    
    
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {'orderid': orderid, 'sku': unknown_sku, 'qty': 20}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.json()['status_code'] == 404
    assert r.json()['detail'] == f'Недопустимый артикул {unknown_sku}'


def test_deallocate(add_stock):
    """
    Сквозной тест для проверки работы конечной точки отмены размещения заказа:
    1) Сперва размещаем заказ в первой партии
    2) Проверям, что размещение второго заказа в той же партии невозможно, так как товара нет в наличии
    3) Отменяем первый заказ
    4) Размещаем второй заказ в той же партии
    """
    sku, order1, order2 = random_sku(), random_orderid(), random_orderid()
    batch = random_batchref()
    add_stock([(batch, sku, 100, '2011-01-02')])
    url = config.get_api_url()
    # fully allocate
    r = requests.post(
        f'{url}/allocate', json={'orderid': order1, 'sku': sku, 'qty': 100}
    )
    assert r.json()['batchref'] == batch

    # cannot allocate second order
    r = requests.post(
        f'{url}/allocate', json={'orderid': order2, 'sku': sku, 'qty': 100}
    )
    assert r.json()['status_code'] == 404

    # deallocate
    r = requests.post(
        f'{url}/deallocate', json={'orderid': order1, 'sku':sku, 'qty': 100}
    )
    assert r.ok
    
    # allocate second order
    r = requests.post(
        f'{url}/allocate', json={'orderid': order2, 'sku': sku, 'qty': 100}
    )
    assert r.ok
    assert r.json()['batchref'] == batch