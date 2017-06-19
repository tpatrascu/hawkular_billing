#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import yaml

from config import config
from user_api import UserAPI
from admin_api import AdminAPI


def start():
    cherrypy.tree.mount(UserAPI(), '/', config=config)
    cherrypy.tree.mount(AdminAPI(), '/admin', config=config)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    start()
