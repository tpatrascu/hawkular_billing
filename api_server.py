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


class UserAPI(object):
    """User API controller"""
    @cherrypy.expose
    def index(self):
        return "user api"


class AdminAPI(object):
    """Admin API controller"""
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return "admin api"


def start():
    cherrypy.tree.mount(UserAPI(), '/', config=config)
    cherrypy.tree.mount(AdminAPI(), '/admin', config=config)
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

    start()
