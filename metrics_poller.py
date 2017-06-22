#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from celery import group
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

import model.db as db
from model.tenant import Tenant
from model.metric import Metric

from config import config
from utils import dget, redis_lock, hawkular_client, metric_types_map


# Init Celery
redis_url = 'redis://{0}:{1}/{2}'.format(
    config['metrics_poller']['redis_host'],
    config['metrics_poller']['redis_port'],
    config['metrics_poller']['redis_queue_db']
)
app = Celery('tasks', broker=redis_url)
logger = get_task_logger(__name__)
worker_db_pool = None


@app.on_after_configure.connect
def setup_initial_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        config['metrics_poller']['get_definitions_interval'],
        get_tenants.s())
    sender.add_periodic_task(
        config['metrics_poller']['get_metric_data_interval'],
        run_get_metrics.s())


@worker_process_init.connect
def init_worker_db_pool(sender=None, conf=None, **kwargs):
    global worker_db_pool
    worker_db_pool = db.session_pool()


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
            with db.session_man(worker_db_pool) as session:
                for tenant in tenants:
                    if not session.query(Tenant).filter_by(
                            name=tenant.name).count():
                        session.add(tenant)

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
            logger.info('Run get_metrics_definitions({})'.format(tenant))
            resp = hawkular_client(tenant).query_metric_definitions()

            logger.info('Update metrics DB table for {} tenant'.format(tenant))
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
            with db.session_man(worker_db_pool) as session:
                for metric in metrics:
                    if not session.query(Metric).filter_by(
                            metric_id=metric.metric_id).count():
                        session.add(metric)
                    else:
                        session.query(Metric).filter_by(
                            metric_id=metric.metric_id).update({
                                'min_timestamp': metric.min_timestamp,
                                'max_timestamp': metric.max_timestamp,
                            })
        else:
            logger.info('get_metrics_definitions({}) locked'.format(tenant))


@app.task
def run_get_metrics():
    lock_id = 'run_get_metrics_lock'
    logger.info('Try running run_get_metrics')
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Running run_get_metrics')
            metrics = []
            with db.session_man(worker_db_pool) as session:
                metrics = session.query(Metric).all()

            logger.info('Running get_metric_data tasks for all metrics')
            group(
                get_metrics_definitions.s(metric.tenant, metric.metric_id)
                for metric in metrics
            ).apply_async()
        else:
            logger.info('get_tenants task already running')


@app.task
def get_metric_data(tenant, metric_id, metric_type):
    lock_id = 'metrics_data_{0}_lock'.format(metric_id)
    logger.info('Try running get_metrics_data({})'.format(metric_id))
    with redis_lock(lock_id) as locked:
        if not locked:
            logger.info('Run get_metrics_data({})'.format(metric_id))

            last_db_timestamp = None
            with db.session_man(worker_db_pool) as session:
                last_db_timestamp = session.query.
                with_entities(MetricData.timestamp).filter_by(
                    metric_id=metric_id, tenant=tenant
                ).order_by(timestamp.desc()).first()

            resp = hawkular_client(tenant).query_metric(
                metric_types_map[metric_type],
                metric_id,
                start=-  # now - last_db_timestamp
            )

            logger.info('Update tenants DB table for {} tenant'.format(tenant))
        else:
            logger.info('get_metrics_definitions({}) locked'.format(tenant))
