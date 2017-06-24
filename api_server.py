#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy

from cp_extend.saplugin import SAEnginePlugin
from cp_extend.satool import SATool

from model.db import migrate as db_migrate
from model.tenant import Tenant
from model.metric import Metric
from model.metric_data import MetricData

from config import config

import json
import datetime


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

    def iterencode(self, value):
        # Adapted from cherrypy/_cpcompat.py
        for chunk in super().iterencode(value):
            yield chunk.encode("utf-8")


def json_handler(*args, **kwargs):
    # Adapted from cherrypy/lib/jsontools.py
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return _JSONEncoder().iterencode(value)


class MetricApi(object):
    @cherrypy.expose
    @cherrypy.tools.json_out(handler=json_handler)
    def index(self, tenant, metric):
        db = cherrypy.request.db
        metric = metric.replace('%2f', '/')
        metric = metric.replace('%2F', '/')
        rows = db.query(MetricData.timestamp, MetricData.value) \
            .filter_by(metric_id=metric, tenant=tenant).all()
        return rows


@cherrypy.popargs('metric', handler=MetricApi())
class TenantApi(object):
    @cherrypy.expose
    @cherrypy.tools.json_out(handler=json_handler)
    def index(self, tenant):
        db = cherrypy.request.db
        rows = db.query(Metric.metric_id) \
            .filter_by(tenant=tenant).all()
        return [x[0] for x in rows]


@cherrypy.popargs('tenant', handler=TenantApi())
class UserApiRoot(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        db = cherrypy.request.db
        rows = db.query(Tenant.name).all()
        return [x[0] for x in rows]


def start():
    cherrypy.tree.mount(UserApiRoot(), '/', config=config)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    # Init SQLAlchemy
    connection_string = '{0}://{1}:{2}@{3}/{4}'.format(
        config['database']['driver'],
        config['database']['user'],
        config['database']['password'],
        config['database']['host'],
        config['database']['db']
    )
    engine_args = {
        'isolation_level': 'REPEATABLE_READ',
        'pool_size': config['database']['cp_pool_size'],
        'pool_recycle': 3600,
    }
    session_args = {'autocommit': False, 'autoflush': True}

    db_migrate(connection_string)

    SAEnginePlugin(cherrypy.engine, connection_string,
                   engine_args, session_args).subscribe()
    cherrypy.tools.db = SATool()

    if '/' in config:
        config['/'].update({'tools.db.on': True})
    else:
        config['/'] = {'tools.db.on': True}

    start()
