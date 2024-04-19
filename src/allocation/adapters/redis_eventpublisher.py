import redis
import logging
import json
from dataclasses import asdict
from src.allocation import config
from src.allocation.domain import events

r = redis.Redis(**config.get_redis_host_and_port())

# публикация событий в канал
def publish(channel, event: events.Event):
    logging.debug('publishing: channel=%s, event=%s', channel, event)
    r.publish(channel, json.dumps(asdict(event)))