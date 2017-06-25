# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from model import Base


class Metric(Base):
    __tablename__ = 'metrics'

    metric_id = Column(String(512), primary_key=True)
    tenant = Column(String(512), ForeignKey('tenants.name'), primary_key=True)
    descriptor_name = Column(String(512))
    nodename = Column(String(512))
    labels = Column(String(512))
    pod_name = Column(String(512))
    object_type = Column(String(512))
    metric_type = Column(String(512))
    units = Column(String(50))
    children = relationship("Label")
