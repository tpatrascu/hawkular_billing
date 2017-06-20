#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from celery import group
from celery.utils.log import get_task_logger
import redis

from hawkular.metrics import HawkularMetricsClient, MetricType

from model.db_pool import db_session
from model.tenant import Tenant
from model.metric import Metric

from contextlib import contextmanager
from config import config
from utils import dget

LOCK_EXPIRE = 10 * 60

# Init Celery
redis_url = 'redis://{0}:{1}/{2}'.format(
    config['metrics_poller']['redis_host'],
    config['metrics_poller']['redis_port'],
    config['metrics_poller']['redis_queue_db']
)
app = Celery('tasks', broker=redis_url)
logger = get_task_logger(__name__)


def hawkular_client(tenant_id=''):
    return HawkularMetricsClient(
        tenant_id=tenant_id,
        scheme=config['hawkular_metrics_client']['scheme'],
        host=config['hawkular_metrics_client']['host'],
        port=config['hawkular_metrics_client']['port'],
        path=config['hawkular_metrics_client']['path'],
        token=config['hawkular_metrics_client']['token']
    )


@app.on_after_configure.connect
def setup_initial_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        config['metrics_poller']['get_namespaces_interval'],
        get_tenants.s())


@contextmanager
def redis_lock(lock_id):
    """ Redis lock manager to ensure only one instance of a task is running """
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


@app.task
def get_tenants():
    lock_id = 'get_tenants_lock'
    logger.info('Try running get_tenants')
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Running get_tenants')

            logger.info('Updating tenants DB table')
            tenant_ids = [x['id'] for x in hawkular_client().query_tenants()]
            tenants = map(lambda x: Tenant(name=x), tenant_ids)
            for tenant in tenants:
                if not db_session.query(Tenant).filter_by(
                        name=tenant.name).count():
                    db_session.add(tenant)
                    db_session.commit()

            logger.info('Running get_metrics_definitions tasks on tenants')
            group(
                get_metrics_definitions.s(tenant) for tenant in tenant_ids
            ).apply_async()
        else:
            logger.info('get_tenants task already running')


@app.task
def get_metrics_definitions(tenant):
    lock_id = 'metrics_definitions_{0}_lock'.format(tenant)
    logger.info('Try running get_metrics_definitions')
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Running get_metrics_definitions')
            resp = hawkular_client(tenant).query_metric_definitions()

            logger.info('Updating tenants DB table')
            metrics = map(
                lambda x: Metric(
                    metric_id=x['id'].replace('/', '%2F'),
                    descriptor_name=dget(x, ['tags', 'descriptor_name']),
                    nodename=dget(x, ['tags', 'nodename']),
                    labels=dget(x, ['tags', 'labels']),
                    tenant=x.get('tenantId', None),
                    pod_name=dget(x, ['tags', 'pod_name']),
                    object_type=dget(x, ['tags', 'type']),
                    metric_type=x.get('type', None),
                    units=dget(x, ['tags', 'units']),
                    min_timestamp=x.get('minTimestamp', None),
                    max_timestamp=x.get('maxTimestamp', None)
                ), resp)
            for metric in metrics:
                if not db_session.query(Metric).filter_by(
                        metric_id=metric.metric_id).count():
                    db_session.add(metric)
                    db_session.commit()
                else:
                    db_session.query(Metric).filter_by(
                        metric_id=metric.metric_id).update({
                            'min_timestamp': metric.min_timestamp,
                            'max_timestamp': metric.max_timestamp,
                        })
                    db_session.commit()
        else:
            logger.info('get_metrics_definitions task already running')
