# Сквозные тесты Е2Е для всего, что связано с вебом

import pytest
import requests

from src.allocation import config
from . import api_client
from tests.random_refs import random_batchref, random_orderid, random_sku


class TestAllocate:
    def test_happy_path_returns_200_and_allocated_batch(postgres_db):
        """
        Первый сквозной тест для проверки использования конечной точки API 
        и связывания с реальной БД
        """
        # random_sku(), random_batchref - вспомогательные функции для генерации строки для артикула и ссылки
        # используются как один из способов предотвратить влияние различных тестов и запусков друг на друга при работа с реальной БД
        orderid = random_orderid()
        sku, othersku = random_sku(), random_sku('other')
        earlybatch = random_batchref(1)
        laterbatch = random_batchref(2)
        otherbatch = random_batchref(3)

        api_client.post_to_add_batch(laterbatch, sku, 100, '2011-01-02')
        api_client.post_to_add_batch(earlybatch, sku, 100, '2011-01-01')
        api_client.post_to_add_batch(otherbatch, othersku, 100, None)

        r = api_client.post_to_allocate(orderid, sku, 3)
        
        assert r.status_code == 200
        assert r.json()['batchref'] == earlybatch

        r = api_client.get_allocation(orderid)
        assert r.ok
        assert r.json() == [
            {'sku': sku, 'batchref': earlybatch}
        ]
        

    def test_unhappy_path_returns_400_and_error_message(postgres_db):
        unknown_sku, orderid = random_sku(), random_orderid()
        r = api_client.post_to_allocate(orderid, unknown_sku, 3, expect_success=False)
        assert r.status_code == 404
        assert r.json()['detail'] == f'Недопустимый артикул {unknown_sku}'

        r = api_client.get_allocation(orderid)
        assert r.status_code == 404


class TestDeallocate:
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
        api_client.post_to_add_batch(batch, sku, 100, '2011-01-02')
        # fully allocate
        r = api_client.post_to_allocate(order1, sku, 100)
        assert r.json()['batchref'] == batch

        # cannot allocate second order
        r = api_client.post_to_allocate(order2, sku, 100)
        # assert r.json()['status_code'] == 404
        assert r.json()['batchref'] == None
    

        # deallocate
        r = api_client.post_to_deallocate(order1, sku, 100)
        assert r.ok
        
        # allocate second order
        r = api_client.post_to_allocate(order2, sku, 100)
        assert r.ok
        assert r.json()['batchref'] == batch