"""发音评测 ORM 模型 — pronunciation_content + pronunciation_records 表"""

from sqlalchemy import (
    Column, Integer, String, Enum, JSON, DateTime, Text, DECIMAL, ForeignKey, func
)
from app.core.database import Base


class PronunciationContent(Base):
    """跟读内容库 — 单词/句子跟读素材"""
    __tablename__ = "pronunciation_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="内容标题")
    content_text = Column(Text, nullable=False, comment="跟读文本")
    content_type = Column(
        Enum("word", "sentence", name="pronunciation_content_type_enum"),
        nullable=False, comment="内容类型：单词/句子",
    )
    cefr_level = Column(String(5), nullable=False, comment="CEFR 难度：A1/A2/B1/B2/C1/C2")
    category = Column(String(64), default=None, comment="分类：日常/商务/旅行/学术等")
    phonetic_ipa = Column(String(500), default=None, comment="IPA 音标")
    audio_url = Column(String(500), default=None, comment="标准发音音频 URL")
    tags = Column(JSON, default=None, comment="标签数组")
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PronunciationRecord(Base):
    """发音评测记录 — 每次跟读评分结果"""
    __tablename__ = "pronunciation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("pronunciation_content.id"), nullable=False)
    mode = Column(
        Enum("word", "sentence", name="pronunciation_mode_enum"),
        nullable=False, comment="评测模式",
    )
    audio_url = Column(String(500), default=None, comment="用户录音文件路径")
    transcript = Column(Text, default=None, comment="ASR 转写文本")
    overall_score = Column(DECIMAL(5, 2), nullable=False, comment="综合分 0-100")
    phoneme_score = Column(DECIMAL(5, 2), default=None, comment="音素准确度分数")
    stress_score = Column(DECIMAL(5, 2), default=None, comment="重音位置分数")
    linking_score = Column(DECIMAL(5, 2), default=None, comment="连读表现分数（仅句子）")
    intonation_score = Column(DECIMAL(5, 2), default=None, comment="语调曲线分数")
    rhythm_score = Column(DECIMAL(5, 2), default=None, comment="节奏感分数")
    error_phonemes = Column(JSON, default=None, comment="错误音素列表 JSON")
    correction_advice = Column(Text, default=None, comment="纠音建议文本")
    teacher_review = Column(Text, default=None, comment="教师点评")
    teacher_score = Column(DECIMAL(5, 2), default=None, comment="教师评分")
    created_at = Column(DateTime, server_default=func.now())
