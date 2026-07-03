"""学习资料 ORM 模型 — learning_materials + material_records 表

注意：daily_tasks 已在 knowledge_graph.py 中定义（DailyTask），
material_recommendations 已在 knowledge_graph.py 中定义（MaterialRecommendation）。
本文件仅定义需求说明书中剩余的 learning_materials 和 material_records。
"""

from sqlalchemy import (
    Column, Integer, String, Enum, JSON, DateTime, Text, DECIMAL, ForeignKey, func
)
from app.core.database import Base


class LearningMaterial(Base):
    """学习资料库 — 视频/文章/音频三类"""
    __tablename__ = "learning_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="资料标题")
    description = Column(Text, default=None, comment="资料描述")
    material_type = Column(
        Enum("video", "article", "audio", name="material_type_enum"),
        nullable=False, comment="资料类型",
    )
    url = Column(String(500), nullable=False, comment="资料链接")
    cefr_level = Column(String(5), nullable=False, comment="CEFR 难度")
    category = Column(String(64), default=None, comment="分类标签")
    tags = Column(JSON, default=None, comment="标签数组")
    duration_seconds = Column(Integer, default=None, comment="时长（秒），视频/音频适用")
    focus_dimensions = Column(JSON, default=None, comment="聚焦维度：speaking/reading/grammar")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MaterialRecord(Base):
    """资料学习记录 — 用户浏览/完成资料的记录"""
    __tablename__ = "material_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("learning_materials.id"), nullable=False)
    action = Column(
        Enum("viewed", "completed", "disliked", name="material_action_enum"),
        default="viewed", nullable=False,
    )
    duration_seconds = Column(Integer, default=None, comment="实际学习时长")
    created_at = Column(DateTime, server_default=func.now())
