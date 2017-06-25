# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float, TIMESTAMP
from model import Base


class MetricData(Base):
    __tablename__ = 'metrics_data'

    metric_id = Column(String(512), primary_key=True)
    timestamp = Column(TIMESTAMP, primary_key=True)
    tenant = Column(String(512), index=True)
    value = Column(Float)
