# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from model import Base


class Namespace(Base):
    __tablename__ = 'namespaces'

    name = Column(String(512), primary_key=True)
