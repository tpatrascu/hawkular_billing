# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from model import Base


class MetricData(Base):
    __tablename__ = 'metrics_data'

    metric_id = Column(String(512))
    tenant = Column(String(512))
    timestamp = Column(TIMESTAMP)
    value = Column(Float)
