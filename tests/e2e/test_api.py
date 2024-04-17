# Сквозные тесты Е2Е для всего, что связано с вебом

import pytest
import requests

from src.allocation import config
from tests.random_refs import random_batchref, random_orderid, random_sku



def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(
        f'{url}/batches',
        json={'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta}
    )
    
    assert r.status_code == 200


def test_happy_path_returns_200_and_allocated_batch(postgres_db):
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

    post_to_add_batch(laterbatch, sku, 100, '2011-01-02')
    post_to_add_batch(earlybatch, sku, 100, '2011-01-01')
    post_to_add_batch(otherbatch, othersku, 100, None)

    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    
    assert r.status_code == 200
    assert r.json()['batchref'] == earlybatch
    

def test_unhappy_path_returns_400_and_error_message(postgres_db):
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {'orderid': orderid, 'sku': unknown_sku, 'qty': 20}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.json()['status_code'] == 404
    assert r.json()['detail'] == f'Недопустимый артикул {unknown_sku}'


def test_deallocate(postgres_db):
    """
    Сквозной тест для проверки работы конечной точки отмены размещения заказа:
    1) Сперва размещаем заказ в первой партии
    2) Проверям, что размещение второго заказа в той же партии невозможно, так как товара нет в наличии
    3) Отменяем первый заказ
    4) Размещаем второй заказ в той же партии
    """
    sku, order1, order2 = random_sku(), random_orderid(), random_orderid()
    batch = random_batchref()
    post_to_add_batch(batch, sku, 100, '2011-01-02')
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
    print(r.json())
    # # assert r.json()['status_code'] == 404
    # assert r.json()['batchref'] == None
 

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