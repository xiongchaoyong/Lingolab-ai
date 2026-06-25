"""后台管理 ORM 模型 — classes / class_students / assignments / assignment_submissions / admin_logs"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL, JSON, Enum as SAEnum, SmallInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class Class(Base):
    """班级表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="班级名称")
    description = Column(String(500), default="", comment="班级描述")
    teacher_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    invite_code = Column(String(20), nullable=False, unique=True, comment="邀请码")
    invite_expires_at = Column(DateTime, default=None, comment="邀请码过期时间")
    level_range = Column(String(20), default="", comment="等级范围")
    student_count = Column(SmallInteger, default=0, comment="学生数")
    is_active = Column(Integer, default=1, comment="0-停用 1-启用")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    teacher = relationship("UserProfile", backref="teaching_classes")


class ClassStudent(Base):
    """班级学生表"""
    __tablename__ = "class_students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="class_memberships")
    class_ = relationship("Class", backref="students")


class Assignment(Base):
    """作业表"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    title = Column(String(200), nullable=False, comment="作业标题")
    description = Column(Text, default=None, comment="作业描述")
    content_type = Column(SAEnum("pronunciation", "conversation", "dubbing"), nullable=False)
    content_ids = Column(JSON, nullable=False, comment="指定内容ID数组")
    due_date = Column(DateTime, default=None, comment="截止时间")
    completion_rate = Column(DECIMAL(4, 1), default=0.0, comment="完成率百分比")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    class_ = relationship("Class", backref="assignments")


class AssignmentSubmission(Base):
    """作业提交表"""
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    audio_url = Column(String(500), default=None, comment="录音文件路径")
    score = Column(DECIMAL(5, 2), default=None, comment="AI评分")
    teacher_feedback = Column(Text, default=None, comment="教师点评")
    teacher_score = Column(DECIMAL(5, 2), default=None, comment="教师评分")
    status = Column(SAEnum("submitted", "reviewed"), default="submitted")
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="assignment_submissions")
    assignment = relationship("Assignment", backref="submissions")


class AdminLog(Base):
    """管理员操作日志表"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    action = Column(String(100), nullable=False, comment="操作类型")
    target_type = Column(String(50), nullable=False, comment="操作对象类型")
    target_id = Column(Integer, default=None, comment="操作对象ID")
    detail = Column(Text, default=None, comment="操作详情JSON")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    admin = relationship("UserProfile", backref="admin_logs")