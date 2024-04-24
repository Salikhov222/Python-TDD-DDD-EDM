import redis
import logging
import json
from dataclasses import asdict
from src.allocation import config
from src.allocation.domain import events

r = redis.Redis(**config.get_redis_host_and_port())

CHANNEL_MAPPING = {
    events.Allocated: "line_allocated"
}

# публикация событий в канал
def publish(event: events.Event):
    channel = CHANNEL_MAPPING.get(type(event))
    if channel:
        logging.debug('publishing: channel=%s, event=%s', channel, event)
        print('publishing: channel=%s, event=%s', channel, event)
        r.publish(channel, json.dumps(asdict(event)))
    else:
        logging.warning('No channel defined for event %s', type(event))