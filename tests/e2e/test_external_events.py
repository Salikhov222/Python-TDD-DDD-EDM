import json
import sys
from tenacity import Retrying, stop_after_delay
from tests.random_refs import random_batchref, random_orderid, random_sku
from . import api_client, redis_client

class TestRedis:

    # TODO: поднять для данного теста контейнер redis_pubsub в Docker
    def test_change_batch_quantity_leading_to_reallocation(self, postgres_db):    
        # начать с двух партий и заказа, размещенного в одной из них
        orderid, sku = random_orderid(), random_sku()
        earlier_batch, later_batch = random_batchref('old'), random_batchref('newer')
        api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')
        api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-02')
        response = api_client.post_to_allocate(orderid, sku, 10)
        assert response.json()['batchref'] == earlier_batch

        subscription = redis_client.subscribe_to('line_allocated')

        # изменить количество товара в размещенной партии,
        # чтобы оно было меньше, чем в заказе
        redis_client.publish_message('change_batch_quantity', {
            'batchref': earlier_batch, 'qty': 5
        })

        # подождать до тех пор, пока мы не увидим сообщение
        # о повторном размещении заказа
        messages = []
        for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
            with attempt:
                message = subscription.get_message(timeout=1)
                if message:
                    messages.append(message)
                data = json.loads(messages[-1]['data'])
                assert data['orderid'] == orderid
                assert data['batchref'] == later_batch


    def test_allocate_via_event_in_redis(self, postgres_db):
        # создание двух партий и размещение в них двух заказов через API и Redis
        orderid_1, orderid_2, sku = random_orderid(1), random_orderid(2), random_sku()
        earlier_batch, later_batch = random_batchref('old'), random_batchref('newer')
        api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')
        api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-02')
        response = api_client.post_to_allocate(orderid_1, sku, 10)
        assert response.json()['batchref'] == earlier_batch

        subscription = redis_client.subscribe_to('line_allocated')

        redis_client.publish_message('allocate', {
            'orderid': orderid_2, 'sku': sku, 'qty': 5
        })

        # подождать до тех пор, пока мы не увидим сообщение
        # о размещении второго заказа
        messages = []
        for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
            with attempt:
                message = subscription.get_message(timeout=1)
                if message:
                    messages.append(message)
                data = json.loads(messages[-1]['data'])
                assert data['orderid'] == orderid_2
