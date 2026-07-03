"""SQLAlchemy 测评模型 — 映射 assessment_questions + assessment_records 表"""

from sqlalchemy import Column, Integer, String, Enum, JSON, DateTime, Text, DECIMAL, ForeignKey, func
from app.core.database import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_option = Column(Integer, nullable=False, comment="正确选项序号 1-4")
    dimension = Column(
        String(20), nullable=False,
        comment="题目维度: pronunciation/fluency/grammar/vocabulary/interaction"
    )
    difficulty = Column(String(5), nullable=False, comment="CEFR难度：A1/A2/B1/B2/C1")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    session_id = Column(String(36), nullable=False, comment="测评会话UUID")
    question_id = Column(Integer, ForeignKey("assessment_questions.id"), nullable=True, comment="题库题目ID（动态生成时为NULL）")
    question_type = Column(
        String(20), nullable=False,
        comment="题目类型: pronunciation/fluency/grammar/vocabulary/interaction"
    )
    user_answer = Column(Text, default=None, comment="选项ID 或 录音URL")
    is_correct = Column(Integer, default=None, comment="客观题是否正确，口语题为NULL")
    score = Column(DECIMAL(5, 2), default=None, comment="该题得分 0-100")
    audio_url = Column(String(500), default=None, comment="口语题录音文件路径")
    transcript = Column(Text, default=None, comment="口语题转写文本")
    question_order = Column(Integer, nullable=False, comment="题号 1-10")
    question_data = Column(JSON, nullable=True, comment="动态生成的题目数据(JSON)")
    created_at = Column(DateTime, server_default=func.now())