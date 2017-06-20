# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Namespace(Base):
    __tablename__ = 'namespaces'

    name = Column(String, primary_key=True)
