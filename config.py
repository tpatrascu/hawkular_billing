# -*- coding: utf-8 -*-

import os
import yaml

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(APP_ROOT, 'config.yaml')
DEFAULT_CONFIG = {
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(APP_ROOT, 'static'),
    },
}


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
                    self.config = {**DEFAULT_CONFIG, **user_config}

    def get_config(self):
        return self.config


config = Config().get_config()
