# -*- coding: utf-8 -*-
"""
DB connection pool for use in non-cherrypy threaded processes
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from model import Base

from contextlib import contextmanager


def pool(connection_string, engine_args=None, session_args=None):
    """
    Initializes and engine with a connection pool
    returns scoped_session factory
    """
    if engine_args is None:
        engine_args = {}
    if session_args is None:
        session_args = {}

    engine = create_engine(
        connection_string, convert_unicode=True, **engine_args)

    return scoped_session(sessionmaker(bind=engine, **session_args))


def migrate(connection_string):
    engine = create_engine(
        connection_string, convert_unicode=True,
        pool_recycle=3600, pool_size=10)
    Base.metadata.create_all(engine)
    engine.dispose()


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
    except Exception:
        session.rollback()
        raise
    finally:
        ScopedSession.remove()
