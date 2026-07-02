"""智能客服 ORM 模型 — faq_entries + support_sessions + security_logs 表"""

from sqlalchemy import (
    Column, Integer, String, Enum, JSON, DateTime, Text, ForeignKey, func
)
from app.core.database import Base


class FAQEntry(Base):
    """FAQ 条目 — 预设常见问题"""
    __tablename__ = "faq_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False, comment="问题文本")
    answer = Column(Text, nullable=False, comment="回答文本")
    category = Column(
        Enum("product_use", "study_advice", "tech_issue", "refund", "general",
             name="faq_category_enum"),
        nullable=False, comment="问题分类",
    )
    sort_order = Column(Integer, default=0, comment="排序权重")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SupportSession(Base):
    """客服会话 — 用户与 AI 客服的对话记录"""
    __tablename__ = "support_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    question = Column(Text, nullable=False, comment="用户提问")
    answer = Column(Text, default=None, comment="AI 回答")
    category = Column(String(32), default=None, comment="问题分类")
    need_manual = Column(Integer, default=0, nullable=False, comment="是否需要转人工")
    input_mode = Column(
        Enum("text", "voice", name="support_input_mode_enum"),
        default="text", nullable=False, comment="输入方式",
    )
    created_at = Column(DateTime, server_default=func.now())


class SecurityLog(Base):
    """安全日志 — 敏感操作和违规记录"""
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), default=None)
    event_type = Column(
        Enum("sensitive_content", "rate_limit", "auth_failure", "suspicious_input",
             name="security_event_enum"),
        nullable=False, comment="事件类型",
    )
    detail = Column(Text, default=None, comment="事件详情")
    ip_address = Column(String(45), default=None, comment="IP 地址")
    created_at = Column(DateTime, server_default=func.now())
