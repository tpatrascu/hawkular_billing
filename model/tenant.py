# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from model import Base


class Tenant(Base):
    __tablename__ = 'tenants'

    name = Column(String(512), primary_key=True)
    children = relationship("Metric")
