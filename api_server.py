#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import yaml

from config import config


class UserAPI(object):
    """User API controller"""
    @cherrypy.expose
    def index(self):
        return "user api"


class AdminAPI(object):
    """Admin API controller"""
    @cherrypy.expose
    def index(self):
        return "admin api"


def start():
    cherrypy.tree.mount(UserAPI(), '/', config=config)
    cherrypy.tree.mount(AdminAPI(), '/admin', config=config)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    start()
