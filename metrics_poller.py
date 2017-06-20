#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from celery.utils.log import get_task_logger
import redis

from hawkular.metrics import HawkularMetricsClient, MetricType

from model.db_pool import db_session
from model.namespace import Namespace

from contextlib import contextmanager
from config import config

LOCK_EXPIRE = 10 * 60

# Init Celery
redis_url = 'redis://{0}:{1}/{2}'.format(
    config['metrics_poller']['redis_host'],
    config['metrics_poller']['redis_port'],
    config['metrics_poller']['redis_queue_db']
)
app = Celery('tasks', broker=redis_url)
logger = get_task_logger(__name__)


@app.on_after_configure.connect
def setup_initial_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        config['metrics_poller']['get_metrics_definitions_interval'],
        get_metrics_definitions.s()
    )
    sender.add_periodic_task(
        config['metrics_poller']['get_namespaces_interval'],
        get_metrics_definitions.s()
    )


def hawkular_client(tenant_id):
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
    r = redis.StrictRedis(
        host=config['metrics_poller']['redis_host'],
        port=config['metrics_poller']['redis_port'],
        db=config['metrics_poller']['redis_lock_db']
    )

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


@app.task
def get_namespaces():
    lock_id = 'get_namespaces_lock'
    logger.info('Try running get_namespaces')
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Running get_namespaces')
            print(hawkular_client('myproject').query_tenants())
        else:
            logger.info('get_namespaces task already running')


@app.task
def get_metrics_definitions():
    lock_id = 'metrics_definitions_lock'
    logger.info('Try running get_metrics_definitions')
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Running get_metrics_definitions')
            print(hawkular_client('myproject').get_metrics_definitions())
        else:
            logger.info('get_metrics_definitions task already running')
