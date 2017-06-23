#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from celery import group
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

import model.db as db
from model.tenant import Tenant
from model.metric import Metric
from model.metric_data import MetricData

from config import config
from utils import dget, redis_lock, hawkular_client, metric_types_map
from datetime import datetime, timedelta

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
    logger.info('Run get_tenants')
    logger.info('Updating tenants DB table')
    tenant_ids = [x['id'] for x in hawkular_client().query_tenants()]
    tenants = map(lambda x: Tenant(name=x), tenant_ids)
    with db.session_man(worker_db_pool) as session:
        for tenant in tenants:
            if not session.query(Tenant).filter_by(
                    name=tenant.name).count():
                session.add(tenant)

    logger.info('Run update_metrics_definitions tasks on tenants')
    group(
        update_metrics_definitions.s(tenant) for tenant in tenant_ids
    ).apply_async()


@app.task
def update_metrics_definitions(tenant):
    logger.info('Run update_metrics_definitions({})'.format(tenant))
    resp = hawkular_client(tenant).query_metric_definitions()

    logger.info('Update metrics DB table for {} tenant'.format(tenant))

    metrics = map(
        lambda x: Metric(
            metric_id=x['id'],
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

    collect_metrics = config['metrics_poller']['collect_metrics']
    with db.session_man(worker_db_pool) as session:
        for metric in metrics:
            if (metric.metric_type in collect_metrics.keys() and
                metric.descriptor_name in collect_metrics[metric.metric_type]):
                if not session.query(Metric).filter_by(
                        metric_id=metric.metric_id).count():
                    session.add(metric)
                else:
                    session.query(Metric).filter_by(
                        metric_id=metric.metric_id).update({
                            'min_timestamp': metric.min_timestamp,
                            'max_timestamp': metric.max_timestamp,
                        })

    logger.info('Clean metric definitions DB table for {} tenant'.
                format(tenant))

    with db.session_man(worker_db_pool) as session:
        for metric in session.query(Metric).all():
            if metric.metric_id not in [x['id'] for x in resp]:
                session.delete(metric)


@app.task
def run_get_metrics():
    logger.info('Run run_get_metrics')
    metrics = []
    with db.session_man(worker_db_pool) as session:
        metrics = session.query(Metric).all()

        logger.info('Run get_metric_data tasks for all metrics')
        group(
            get_metric_data.s(
                metric.tenant,
                metric.metric_id,
                metric.metric_type
            )
            for metric in metrics
        ).apply_async()


@app.task
def get_metric_data(tenant, metric_id, metric_type):
    logger.info('Run get_metrics_data({},{},{})'.
                format(tenant, metric_id, metric_type))

    last_metric_data = None
    with db.session_man(worker_db_pool) as session:
        last_metric_data = session.query(MetricData.timestamp).filter_by(
            metric_id=metric_id, tenant=tenant
        ).order_by(MetricData.timestamp.desc()).first()

    max_days_old = 31
    if max_days_old in config['metrics_poller']:
        max_days_old = config['metrics_poller']['max_days_old']

    time_start = datetime.utcnow() - timedelta(days=max_days_old)
    if last_metric_data:
        time_start = last_metric_data.timestamp + timedelta(seconds=1)

    resp = hawkular_client(tenant).query_metric(
        metric_types_map[metric_type],
        metric_id,
        start=time_start
    )

    logger.info('Update metrics_data DB table for get_metrics_data({},{},{})'.
                format(tenant, metric_id, metric_type))

    metric_data = map(
        lambda x: MetricData(
            metric_id=metric_id,
            tenant=tenant,
            timestamp=datetime.utcfromtimestamp(int(x.get('timestamp', None))/1000),
            value=x.get('value', None) if x.get('value', None) != 'Empty' else None
        ), resp)

    with db.session_man(worker_db_pool) as session:
        for value in metric_data:
            session.add(value)
