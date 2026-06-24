"""用户技能分数 ORM 模型 — user_skill_scores 表"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, func
from app.core.database import Base


class UserSkillScore(Base):
    """用户技能分数 — 每次练习的维度分数追踪"""

    __tablename__ = "user_skill_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, comment="用户 ID")
    dimension = Column(
        String(32), nullable=False,
        comment="技能维度：listening / speaking / reading / grammar",
    )
    skill_name = Column(
        String(64), nullable=False,
        comment="具体技能名，如 pronunciation:phoneme_accuracy",
    )
    score = Column(DECIMAL(5, 2), nullable=False, comment="分数 0-100")
    source = Column(
        String(32), nullable=False,
        comment="来源：pronunciation / conversation / daily_task / assessment",
    )
    source_id = Column(Integer, default=None, comment="来源记录 ID")
    created_at = Column(DateTime, server_default=func.now())