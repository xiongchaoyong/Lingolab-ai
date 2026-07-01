"""游戏化闯关 ORM 模型 — user_scores / user_badges / dubbing_content / dubbing_records / notices"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Boolean, Date, SmallInteger
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserScore(Base):
    """积分记录表"""
    __tablename__ = "user_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    action_type = Column(String(50), nullable=False, comment="积分行为：daily_task/challenge/dubbing/streak/pronunciation_high/share")
    score = Column(SmallInteger, nullable=False, comment="积分变化值（正为获得，负为扣除）")
    description = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="scores")


class UserBadge(Base):
    """用户徽章表"""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    badge_type = Column(String(50), nullable=False, comment="徽章类型：newcomer/streak/pronunciation_break/progress/dubbing/perfect/scholar")
    badge_name = Column(String(50), nullable=False, comment="徽章名称")
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="badges")


class DubbingContent(Base):
    """配音内容表"""
    __tablename__ = "dubbing_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    source = Column(String(100), default="")
    difficulty = Column(SAEnum("easy", "medium", "hard"), nullable=False)
    duration = Column(SmallInteger, nullable=False, comment="片段时长（秒）5-20")
    subtitle = Column(String(500), nullable=False)
    audio_url = Column(String(500), nullable=False, comment="原声片段文件路径")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DubbingRecord(Base):
    """配音记录表"""
    __tablename__ = "dubbing_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("dubbing_content.id"), nullable=False)
    audio_url = Column(String(500), nullable=False, comment="用户配音文件路径")
    pronunciation_score = Column(DECIMAL(5, 2), default=None)
    intonation_score = Column(DECIMAL(5, 2), default=None)
    emotion_score = Column(DECIMAL(5, 2), default=None)
    total_score = Column(DECIMAL(5, 2), default=None)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="dubbing_records")
    content = relationship("DubbingContent", backref="records")


class LearningPrediction(Base):
    """学习预测表"""
    __tablename__ = "learning_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    current_score = Column(DECIMAL(5, 2), nullable=False, comment="当前综合分数 0-100")
    trend_slope = Column(DECIMAL(6, 3), default=None, comment="趋势斜率（分/天），正为上升")
    target_score = Column(DECIMAL(5, 2), nullable=False, comment="目标分数")
    predicted_days = Column(SmallInteger, default=None, comment="预计达标天数")
    predicted_date = Column(Date, default=None, comment="预计达标日期")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="prediction")


class Notice(Base):
    """通知表"""
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    type = Column(SAEnum("prediction", "alert", "achievement"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(String(500), nullable=False)
    level = Column(SAEnum("info", "warning"), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="notices")