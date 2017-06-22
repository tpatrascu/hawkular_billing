# -*- coding: utf-8 -*-

import redis
from redis.exceptions import RedisError
from hawkular.metrics import HawkularMetricsClient, MetricType
from contextlib import contextmanager
from config import config


def dget(_dict, keys, default=None):
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


def hawkular_client(tenant_id=''):
    return HawkularMetricsClient(
        tenant_id=tenant_id,
        scheme=config['hawkular_metrics_client']['scheme'],
        host=config['hawkular_metrics_client']['host'],
        port=config['hawkular_metrics_client']['port'],
        path=config['hawkular_metrics_client']['path'],
        token=config['hawkular_metrics_client']['token']
    )


@contextmanager
def redis_lock(lock_id):
    """ Redis lock manager to ensure only one instance of a task is running """
    LOCK_EXPIRE = 10 * 60

    r = redis.StrictRedis(
        host=config['metrics_poller']['redis_host'],
        port=config['metrics_poller']['redis_port'],
        db=config['metrics_poller']['redis_lock_db'])

    status = True

    try:
        status = r.get(lock_id)
    except RedisError as e:
        logger.error(str(e))

    if not status:
        try:
            r.setex(lock_id, LOCK_EXPIRE, True)
        except RedisError as e:
            logger.error(str(e))

    yield status

    try:
        r.delete(lock_id)
    except RedisError as e:
        logger.error(str(e))
