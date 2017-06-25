#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from celery import group
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

import model.db as db
from model.tenant import Tenant
from model.label import Label
from model.metric import Metric
from model.metric_data import MetricData

from utils import config
from datetime import datetime, timedelta
import time
import re

from hawkular.metrics import HawkularMetricsClient, MetricType


metric_types_map = {
    'gauge': MetricType.Gauge,
    'counter': MetricType.Counter,
}


def hawkular_client(tenant_id=''):
    return HawkularMetricsClient(
        tenant_id=tenant_id,
        scheme=config['hawkular_metrics_client']['scheme'],
        host=config['hawkular_metrics_client']['host'],
        port=config['hawkular_metrics_client']['port'],
        path=config['hawkular_metrics_client']['path'],
        token=config['hawkular_metrics_client']['token']
    )


def dget(_dict, keys, default=None):
    """Helper function to safely get item from nested dict."""
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


# Init Celery
redis_url = 'redis://{0}:{1}/{2}'.format(
    config['metrics_poller']['redis_host'],
    config['metrics_poller']['redis_port'],
    config['metrics_poller']['redis_queue_db']
)
app = Celery('tasks', broker=redis_url)
logger = get_task_logger(__name__)


# Init SQLAlchemy
connection_string = '{0}://{1}:{2}@{3}/{4}'.format(
    config['database']['driver'],
    config['database']['user'],
    config['database']['password'],
    config['database']['host'],
    config['database']['db']
)
engine_args = {
    'isolation_level': 'READ COMMITTED',
    'pool_size': 5,
    'pool_recycle': 3600,
}
session_args = {'autocommit': False, 'autoflush': False}

db.migrate(connection_string)

db_pool = None


@worker_process_init.connect
def init_worker_db_pool(sender=None, conf=None, **kwargs):
    global db_pool
    db_pool = db.pool(
        connection_string, engine_args, session_args)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    get_tenants.delay()
    sender.add_periodic_task(
        config['metrics_poller']['get_definitions_interval_sec'],
        get_tenants.s())
    sender.add_periodic_task(
        config['metrics_poller']['bucketDuration_sec'],
        run_get_metrics.s())


@app.task
def get_tenants():
    logger.debug('Run get_tenants')
    logger.debug('Updating tenants DB table')
    tenant_ids = [x['id'] for x in hawkular_client().query_tenants()]
    tenants = map(lambda x: Tenant(name=x), tenant_ids)
    with db.session_man(db_pool) as session:
        for tenant in tenants:
            if not session.query(Tenant).filter_by(
                    name=tenant.name).count():
                session.add(tenant)

    logger.debug('Run update_metrics_definitions tasks on tenants')
    group(
        update_metrics_definitions.s(tenant) for tenant in tenant_ids
    ).apply_async()


@app.task
def update_metrics_definitions(tenant):
    logger.debug('Run update_metrics_definitions({})'.format(tenant))
    resp = hawkular_client(tenant).query_metric_definitions()

    logger.debug('Update metrics DB table for {} tenant'.format(tenant))

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
            units=dget(x, ['tags', 'units'])
        ), resp)

    collect_metrics = config['metrics_poller']['collect_metrics']
    with db.session_man(db_pool) as session:
        for metric in metrics:
            if (metric.metric_type in collect_metrics.keys() and
                metric.descriptor_name in collect_metrics[metric.metric_type]):
                if not session.query(Metric).filter_by(
                        metric_id=metric.metric_id).count():
                    session.add(metric)

    logger.debug('Check for expired metric definitions in {} tenant'.
                 format(tenant))

    with db.session_man(db_pool) as session:
        for metric in session.query(Metric).filter_by(tenant=tenant).all():
            if metric.metric_id not in [x['id'] for x in resp]:
                logger.debug('deleting {}'.format(metric.metric_id))
                session.delete(metric)

        session.commit()

        # parse labels and insert into DB
        for metric in resp:
            if 'labels' in metric['tags']:
                labels = metric['tags']['labels'].split(',')
                for label in labels:
                    label_data = {
                        'key': label.split(':')[0],
                        'value': label.split(':')[1],
                        'metric_id': metric['id'],
                        'tenant': metric['tenantId'],
                    }
                    if not session.query(Label).filter_by(**label_data).count():
                        session.add(Label(**label_data))


@app.task
def run_get_metrics():
    logger.debug('Run run_get_metrics')
    metrics = []
    with db.session_man(db_pool) as session:
        metrics = session.query(Metric).all()

        logger.debug('Run get_metric_data tasks for all metrics')
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
    logger.debug('Run get_metrics_data({},{},{})'.
                 format(tenant, metric_id, metric_type))

    last_metric_data = None
    with db.session_man(db_pool) as session:
        last_metric_data = session.query(MetricData.timestamp).filter_by(
            metric_id=metric_id, tenant=tenant
        ).order_by(MetricData.timestamp.desc()).first()

    max_days_old = 7
    if max_days_old in config['metrics_poller']:
        max_days_old = config['metrics_poller']['max_days_old']

    time_start = datetime.utcnow() - timedelta(days=max_days_old)
    next_delta = config['metrics_poller']['bucketDuration_sec'] + 1
    if last_metric_data:
        time_start = last_metric_data.timestamp + timedelta(seconds=next_delta)

    try:
        resp = hawkular_client(tenant).query_metric_stats(
            metric_types_map[metric_type],
            metric_id,
            start=time_start,
            bucketDuration='{}s'.format(
                config['metrics_poller']['bucketDuration_sec'])
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        logger.error(str(e))
        return

    logger.debug('Update metrics_data DB table for get_metrics_data({},{},{})'.
                 format(tenant, metric_id, metric_type))

    metric_data = map(
        lambda x: MetricData(
            metric_id=metric_id,
            tenant=tenant,
            timestamp=datetime.utcfromtimestamp(x.get('start', 0)/1000),
            value=x.get('avg', None)
        ), resp)

    with db.session_man(db_pool) as session:
        for bucket in metric_data:
            if bucket.value:
                session.add(bucket)
