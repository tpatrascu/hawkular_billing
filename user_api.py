# -*- coding: utf-8 -*-

import cherrypy


class UserAPI(object):
    """User API controller"""
    @cherrypy.expose
    def index(self):
        return "user api"
