# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from model import Base


class Metric(Base):
    __tablename__ = 'metrics'

    metric_id = Column(String(512), primary_key=True)
    descriptor_name = Column(String(512))
    nodename = Column(String(512))
    labels = Column(String(512))
    tenant = Column(String(512), ForeignKey('tenants.name'))
    pod_name = Column(String(512))
    object_type = Column(String(512))
    metric_type = Column(String(512))
    units = Column(String(50))
    min_timestamp = Column(Float)
    max_timestamp = Column(Float)
