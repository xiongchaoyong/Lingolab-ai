"""知识图谱 ORM 模型 — kg_nodes + kg_edges + daily_tasks + material_recommendations"""

from sqlalchemy import (
    Column, Integer, String, Enum, JSON, DateTime, Date,
    DECIMAL, ForeignKey, Text, func
)
from app.core.database import Base


class KGNode(Base):
    """知识图谱节点 — 技能/资料/场景/等级"""
    __tablename__ = "kg_nodes"

    id = Column(String(64), primary_key=True, comment="节点 ID，如 skill:th_sound, material:video_1")
    type = Column(
        Enum("skill", "material", "topic", "cefr_level", "task_type", name="kg_node_type_enum"),
        nullable=False,
        comment="节点类型",
    )
    sub_type = Column(String(32), default=None, comment="子类型：phoneme/grammar/vocabulary/video/article/audio/scene")
    label = Column(String(128), nullable=False, comment="显示名称")
    extra_data = Column(JSON, default=None, comment="附加属性")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class KGEdge(Base):
    """知识图谱边 — 节点间关系"""
    __tablename__ = "kg_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(64), ForeignKey("kg_nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String(64), ForeignKey("kg_nodes.id", ondelete="CASCADE"), nullable=False)
    relation = Column(
        Enum("HAS_PREREQ", "BELONGS_TO", "TEACHES", "COVERS", "SIMILAR_TO", "PRACTICES",
             name="kg_edge_relation_enum"),
        nullable=False,
    )
    weight = Column(DECIMAL(5, 2), default=1.00, comment="权重 0.00-1.00")
    extra_data = Column(JSON, default=None, comment="附加属性")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class DailyTask(Base):
    """每日学习任务 — 行存储替代 JSON"""
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    task_date = Column(Date, nullable=False, comment="任务日期")
    task_type = Column(
        Enum("shadowing", "conversation", "listening", name="task_type_enum"),
        nullable=False,
    )
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, default=None, comment="任务描述")
    difficulty = Column(String(5), default=None, comment="CEFR 难度")
    focus_skill_id = Column(String(64), ForeignKey("kg_nodes.id"), default=None, comment="聚焦技能节点")
    material_id = Column(String(64), ForeignKey("kg_nodes.id"), default=None, comment="关联资料节点")
    scene = Column(String(32), default=None, comment="对话场景 self_intro/restaurant/...")
    status = Column(
        Enum("pending", "skipped", "completed", name="daily_task_status_enum"),
        default="pending",
        nullable=False,
    )
    score = Column(DECIMAL(5, 2), default=None, comment="完成得分")
    duration_seconds = Column(Integer, default=None, comment="完成耗时（秒）")
    skip_reason = Column(String(64), default=None, comment="跳过原因")
    completed_at = Column(DateTime, default=None)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MaterialRecommendation(Base):
    """资料推荐记录"""
    __tablename__ = "material_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    material_node_id = Column(String(64), ForeignKey("kg_nodes.id"), nullable=False)
    recommend_date = Column(Date, nullable=False)
    recommend_score = Column(DECIMAL(5, 2), nullable=False, comment="推荐综合分 0-100")
    reason_tags = Column(JSON, default=None, comment="推荐原因标签数组")
    action = Column(
        Enum("pending", "viewed", "completed", "disliked", name="recommend_action_enum"),
        default="pending",
    )
    viewed_at = Column(DateTime, default=None)
    created_at = Column(DateTime, server_default=func.now())