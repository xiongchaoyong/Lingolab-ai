"""智能对话 ORM 模型 — conversation_sessions + conversation_messages 表"""

from sqlalchemy import (
    Column, Integer, String, Enum, JSON, DateTime, Text, DECIMAL, ForeignKey, func
)
from app.core.database import Base


class ConversationSession(Base):
    """对话会话 — 一次完整的场景对话"""
    __tablename__ = "conversation_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    session_uuid = Column(String(36), unique=True, nullable=False, comment="会话 UUID")
    scene = Column(
        Enum("self_intro", "directions", "shopping", "restaurant", "free",
             name="conversation_scene_enum"),
        nullable=False, comment="对话场景",
    )
    role_id = Column(Integer, default=None, comment="角色扮演角色 ID（仅角色扮演场景）")
    cefr_level = Column(String(5), default=None, comment="用户 CEFR 等级（难度自适应依据）")
    round_count = Column(Integer, default=0, comment="已完成轮数")
    status = Column(
        Enum("active", "completed", "abandoned", name="session_status_enum"),
        default="active", nullable=False,
    )
    # 对话结束四维评分
    score_pronunciation = Column(DECIMAL(5, 2), default=None, comment="发音得分")
    score_grammar = Column(DECIMAL(5, 2), default=None, comment="语法得分")
    score_vocabulary = Column(DECIMAL(5, 2), default=None, comment="词汇得分")
    score_engagement = Column(DECIMAL(5, 2), default=None, comment="参与度得分")
    score_overall = Column(DECIMAL(5, 2), default=None, comment="综合分")
    improvement_suggestions = Column(Text, default=None, comment="改进建议")
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, default=None)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ConversationMessage(Base):
    """对话消息 — 每轮对话记录"""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), nullable=False)
    round_number = Column(Integer, nullable=False, comment="轮次序号 1-N")
    role = Column(
        Enum("user", "assistant", name="message_role_enum"),
        nullable=False, comment="消息角色",
    )
    content_text = Column(Text, nullable=False, comment="消息文本")
    audio_url = Column(String(500), default=None, comment="音频 URL（用户录音或 TTS）")
    # 语法纠错
    grammar_check = Column(JSON, default=None, comment="语法纠错结果 JSON")
    # 流利度评分
    fluency_scores = Column(JSON, default=None, comment="流利度五维评分 JSON")
    # 单轮评分
    score = Column(DECIMAL(5, 2), default=None, comment="单轮得分")
    created_at = Column(DateTime, server_default=func.now())
