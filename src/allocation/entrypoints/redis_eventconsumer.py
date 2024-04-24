import redis
import logging
import json
from src.allocation import config
from src.allocation.adapters import orm
from src.allocation.domain import commands
from src.allocation.service_layer import messagebus, unit_of_work

r = redis.Redis(**config.get_redis_host_and_port())
logger = logging.getLogger(__name__)


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity', 'allocate')       # подписка клиента (веб-приложения) на каналы
    logging.debug("Subscribed to change_batch_quantity and allocate topic")

    for m in pubsub.listen():       # при получении сообщения вызывается соответсвующий каналу обработчик
        channel = m['channel'].decode('utf-8')
        if channel == 'change_batch_quantity':
            handle_change_quantity(m)
        else:
            handle_allocate(m)
        logging.debug(f"Message: {m}")

def handle_change_quantity(m):
    logging.debug('handling %s', m)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])
    messagebus.MessageBus().handle(cmd, uow)

def handle_allocate(m):
    logging.debug('handling %s', m)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    data = json.loads(m['data'])
    cmd = commands.Allocate(orderid=data['orderid'], sku=data['sku'], qty=data['qty'])
    messagebus.MessageBus().handle(cmd, uow)


if __name__ == "__main__":
    main()
