"""SQLAlchemy 用户模型 — 映射 user_profiles 表"""

from sqlalchemy import Column, Integer, String, Enum, JSON, DateTime, func
from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(
        Enum("儿童", "青少年", "大学生", "职场", "中老年", name="age_group_enum"),
        nullable=False,
    )
    learning_goal = Column(
        Enum("日常交流", "考试", "商务", "出国", "兴趣爱好", name="learning_goal_enum"),
        nullable=False,
    )
    interests = Column(JSON, default=None)
    level_self = Column(String(10), default=None)
    level_test = Column(String(5), default=None)
    level_final = Column(String(5), default=None)
    role = Column(
        Enum("learner", "teacher", "admin", name="role_enum"),
        default="learner",
        nullable=False,
    )
    assessment_completed = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())