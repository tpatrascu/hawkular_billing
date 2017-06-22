# -*- coding: utf-8 -*-
"""
DB connection pool for use in non-cherrypy threaded processes
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

# Import models here to run migrations on them
from model import Base
from model.tenant import Tenant
from model.metric import Metric
from model.metric_data import MetricData

from contextlib import contextmanager
from config import config

sa_connect_str = '{0}://{1}:{2}@{3}/{4}'.format(
    config['database']['driver'],
    config['database']['user'],
    config['database']['password'],
    config['database']['host'],
    config['database']['db']
)

# Run DB migrations
engine = create_engine(
    sa_connect_str, convert_unicode=True,
    pool_recycle=3600, pool_size=10)
Base.metadata.create_all(engine)
engine.dispose()


def session_pool():
    """
    Initializes and engine with a connection pool
    returns scoped_session factory
    """
    engine = create_engine(
        sa_connect_str, convert_unicode=True,
        pool_recycle=3600, pool_size=config['database']['pool_size'])

    return scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine))


@contextmanager
def session_man(ScopedSession):
    """
    Provide a transactional scope around a series of operations
    Requires a scoped_session factory as input
    """
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except (SQLAlchemyError, DBAPIError):
        session.rollback()
        raise
    finally:
        ScopedSession.remove()
