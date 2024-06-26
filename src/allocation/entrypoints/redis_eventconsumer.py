import redis
import logging
import json
from src.allocation import config
from src.allocation.bootstrap import bus
from src.allocation.domain import commands

r = redis.Redis(**config.get_redis_host_and_port())
logger = logging.getLogger(__name__)


def main():

    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity', 'allocate')       # подписка клиента (веб-приложения) на каналы
    logging.debug("Subscribed to change_batch_quantity and allocate topic")
    for m in pubsub.listen():       # при получении сообщения вызывается соответсвующий каналу обработчик
        channel = m['channel'].decode('utf-8')
        if channel == 'change_batch_quantity':
            handle_change_quantity(m, bus)
        else:
            handle_allocate(m, bus)
        logging.debug(f"Message: {m}")

def handle_change_quantity(m, bus):
    logging.debug('handling %s', m)
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])
    bus.handle(cmd)

def handle_allocate(m, bus):
    logging.debug('handling %s', m)
    data = json.loads(m['data'])
    cmd = commands.Allocate(orderid=data['orderid'], sku=data['sku'], qty=data['qty'])
    bus.handle(cmd)


if __name__ == "__main__":
    main()
