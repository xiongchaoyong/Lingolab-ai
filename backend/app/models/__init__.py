"""数据库模型 — 所有表继承自此模块的 Base"""

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


class TimestampMixin:
    """所有表的通用字段 mixin"""
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
