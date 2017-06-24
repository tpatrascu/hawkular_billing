# -*- coding: utf-8 -*-

import os
import re
import yaml

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
