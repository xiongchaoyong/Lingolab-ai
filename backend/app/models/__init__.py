"""数据库模型 — 所有表继承自此模块的 Base

导入所有模型确保 SQLAlchemy Base.metadata 能发现全部表。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


class TimestampMixin:
    """所有表的通用字段 mixin"""
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# 导入所有模型，确保 Base.metadata 能发现全部表
from app.models.user import UserProfile  # noqa: E402, F401
from app.models.profile import UserSkillScore  # noqa: E402, F401
from app.models.assessment import AssessmentQuestion, AssessmentRecord  # noqa: E402, F401
from app.models.knowledge_graph import KGNode, KGEdge, DailyTask, MaterialRecommendation  # noqa: E402, F401
from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission, AdminLog  # noqa: E402, F401
from app.models.pronunciation import PronunciationContent, PronunciationRecord  # noqa: E402, F401
from app.models.conversation import ConversationSession, ConversationMessage  # noqa: E402, F401
from app.models.learning import LearningMaterial, MaterialRecord  # noqa: E402, F401
from app.models.gamification import (  # noqa: E402, F401
    UserScore, UserBadge, DubbingContent, DubbingRecord,
    LearningPrediction, Notice,
)
from app.models.community import (  # noqa: E402, F401
    VoiceChallenge, ChallengeSubmission,
    DiscussionPost, PostComment, PostLike,
    StudyGroup, GroupMember,
)
from app.models.support import FAQEntry, SupportSession, SecurityLog  # noqa: E402, F401
