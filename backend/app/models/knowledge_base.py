"""知识库 + 检索日志 ORM 模型"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, func
from app.core.database import Base


class KnowledgeDocument(Base):
    """知识库文档"""

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment="文档标题")
    content = Column(Text, nullable=False, comment="文档正文")
    category = Column(
        String(64), default="general",
        comment="分类：product_use / study_advice / tech_issue / refund / general",
    )
    source_type = Column(
        String(32), default="manual",
        comment="来源：faq（FAQ 自动导入）/ manual（人工录入）",
    )
    is_active = Column(Integer, default=1, comment="是否启用 0/1")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SearchLog(Base):
    """客服检索日志"""

    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=True, comment="用户 ID")
    query = Column(String(500), nullable=False, comment="用户提问")
    retrieved_docs = Column(JSON, nullable=True, comment="检索到的文档 ID 和标题列表")
    reply = Column(Text, nullable=True, comment="AI 回复（截取前 200 字）")
    created_at = Column(DateTime, server_default=func.now())
