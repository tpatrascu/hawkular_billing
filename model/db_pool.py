# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# Import models here to run migrations on them
from model import Base
from model.namespace import Namespace

from config import config

# DB connection pool for use in non-cherrypy processes with multiple threads
sa_connect_str = '{0}://{1}:{2}@{3}/{4}'.format(
    config['database']['driver'],
    config['database']['user'],
    config['database']['password'],
    config['database']['host'],
    config['database']['db']
)

engine = create_engine(
    sa_connect_str, convert_unicode=True,
    pool_recycle=3600, pool_size=10)
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))

# Run DB migrations
Base.metadata.create_all(engine)
