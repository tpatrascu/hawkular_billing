# -*- coding: utf-8 -*-

import datetime
import os
import re
import yaml
import json

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(APP_ROOT, 'config.yaml')
DEFAULT_CONFIG = {
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(APP_ROOT, 'static'),
    },
}


def replace_env_vars(config):
    env_var_regexp = re.compile(r'\${(.*)}')
    new_config = {}
    for k, v in config.items():
        if type(v) is dict:
            v = replace_env_vars(v)
        else:
            m = env_var_regexp.search(str(v))
            if m:
                v = os.environ.get(m.group(1))
        new_config[k] = v
    return new_config


class Config(object):
    """
    Config system.
    Merges default config with the config file, overriding the defaults.
    """
    def __init__(self):
        super(Config, self).__init__()
        self.config = DEFAULT_CONFIG

        if os.path.isfile(DEFAULT_CONFIG_FILE):
            with open(DEFAULT_CONFIG_FILE) as f:
                user_config = yaml.load(f)
                if user_config:
                    user_config = replace_env_vars(user_config)
                    self.config = {**DEFAULT_CONFIG, **user_config}

    def get_config(self):
        return self.config


config = Config().get_config()


def dget(_dict, keys, default=None):
    """Helper function to safely get item from nested dict."""
    for key in keys:
        if isinstance(_dict, dict):
            _dict = _dict.get(key, default)
        else:
            return default
    return _dict


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

    def iterencode(self, value):
        # Adapted from cherrypy/_cpcompat.py
        for chunk in super().iterencode(value):
            yield chunk.encode("utf-8")
