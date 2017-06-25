# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKeyConstraint
from model import Base
from model.metric import Metric


class Label(Base):
    __tablename__ = 'labels'

    key = Column(String(512), primary_key=True)
    value = Column(String(512), primary_key=True)
    tenant = Column(String(512), primary_key=True)
    metric_id = Column(String(512), primary_key=True)
    ForeignKeyConstraint(
        [metric_id, tenant],
        [Metric.metric_id, Metric.tenant])
