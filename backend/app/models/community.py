"""社区服务 ORM 模型 — voice_challenges / challenge_submissions / discussion_posts / post_comments / post_likes / study_groups / group_members"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, SmallInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class VoiceChallenge(Base):
    """语音挑战表"""
    __tablename__ = "voice_challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="挑战标题")
    description = Column(String(500), default="", comment="挑战描述")
    sample_text = Column(String(500), nullable=False, comment="示范文本")
    deadline = Column(DateTime, nullable=False, comment="截止时间")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChallengeSubmission(Base):
    """挑战提交记录表"""
    __tablename__ = "challenge_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("voice_challenges.id"), nullable=False)
    audio_url = Column(String(500), nullable=False, comment="用户录音文件路径")
    pronunciation_score = Column(SmallInteger, default=None, comment="发音分 0-100")
    fluency_score = Column(SmallInteger, default=None, comment="流利度分 0-100")
    total_score = Column(SmallInteger, default=None, comment="综合分 0-100")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="challenge_submissions")
    challenge = relationship("VoiceChallenge", backref="submissions")


class DiscussionPost(Base):
    """讨论帖表"""
    __tablename__ = "discussion_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), default=None, comment="所属小组ID（可选）")
    topic = Column(String(200), nullable=False, comment="帖子标题")
    content = Column(Text, nullable=False, comment="帖子内容")
    likes_count = Column(Integer, default=0, comment="点赞数")
    comments_count = Column(Integer, default=0, comment="评论数")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="discussion_posts")
    comments = relationship("PostComment", backref="post", lazy="dynamic")


class PostComment(Base):
    """帖子评论表"""
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    content = Column(Text, nullable=False, comment="评论内容")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="post_comments")


class PostLike(Base):
    """帖子点赞表"""
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudyGroup(Base):
    """学习小组表 — 映射已有 groups 表"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="小组名称")
    description = Column(String(500), default="", comment="小组简介")
    creator_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    level_range = Column(String(20), default="", comment="等级范围如 A1-C1")
    schedule = Column(String(100), default="", comment="活动时间")
    tags = Column(String(200), default="", comment="标签，逗号分隔")
    max_members = Column(SmallInteger, default=20, comment="最大人数")
    member_count = Column(SmallInteger, default=0, comment="成员数")
    is_archived = Column(Boolean, default=False, comment="是否归档")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class GroupMember(Base):
    """小组成员表 — 映射已有 group_members 表"""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    role = Column(String(10), default="member", comment="owner/member")
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserProfile", backref="group_memberships")
    group = relationship("StudyGroup", backref="members")