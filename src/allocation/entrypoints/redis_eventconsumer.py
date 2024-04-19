import redis
import logging
import json
from src.allocation import config
from src.allocation.adapters import orm
from src.allocation.domain import commands
from src.allocation.service_layer import messagebus, unit_of_work

r = redis.Redis(**config.get_redis_hist_and_port())


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')       # подписка клиетна (веб-приложения) на канал change_batch_quantity

    for m in pubsub.listen():       # при получении сообщения вызывается функция handle_change_quantity()
        handle_change_quantity(m)

def handle_change_quantity(m):
    logging.debug('handling %s', m)
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])
    messagebus.MessageBus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    main()
