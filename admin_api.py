# -*- coding: utf-8 -*-

import cherrypy


class AdminAPI(object):
    """Admin API controller"""
    @cherrypy.expose
    def index(self):
        return "admin api"
