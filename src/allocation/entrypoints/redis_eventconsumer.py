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
    pubsub.subscribe('change_batch_quantity')       # подписка клиента (веб-приложения) на канал change_batch_quantity
    logging.debug("Subscribed to change_batch_quantity topic")

    for m in pubsub.listen():       # при получении сообщения вызывается функция handle_change_quantity()
        handle_change_quantity(m)
        logging.debug(f"Message: {m}")

def handle_change_quantity(m):
    logging.debug('handling %s', m)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])
    messagebus.MessageBus().handle(cmd, uow)


if __name__ == "__main__":
    main()
