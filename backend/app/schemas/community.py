"""社区服务 — 请求/响应 Schema"""

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# 语音挑战
# ============================================================

class ChallengeItem(BaseModel):
    """挑战信息"""
    id: int
    title: str
    description: str = ""
    sample_text: str
    deadline: str
    is_active: bool = True
    participants_count: int = 0
    created_at: str = ""


class ChallengeListResponse(BaseModel):
    """挑战列表"""
    challenges: List[ChallengeItem] = Field(default_factory=list)


class SubmissionItem(BaseModel):
    """提交记录"""
    id: int
    user_id: int
    username: str = ""
    challenge_id: int
    audio_url: str
    pronunciation_score: Optional[int] = None
    fluency_score: Optional[int] = None
    total_score: Optional[int] = None
    created_at: str = ""


class LeaderboardItem(BaseModel):
    """排行榜条目"""
    rank: int
    user_id: int
    username: str
    total_score: Optional[int] = None
    created_at: str = ""


class LeaderboardResponse(BaseModel):
    """排行榜"""
    challenge_id: int
    leaderboard: List[LeaderboardItem] = Field(default_factory=list)


class SubmissionResult(BaseModel):
    """提交结果"""
    submission: SubmissionItem
    rank: Optional[int] = None


# ============================================================
# 话题讨论
# ============================================================

class PostItem(BaseModel):
    """帖子信息"""
    id: int
    user_id: int
    username: str = ""
    avatar: str = ""
    topic: str
    content: str
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    created_at: str = ""
    updated_at: str = ""


class PostListResponse(BaseModel):
    """帖子列表"""
    posts: List[PostItem] = Field(default_factory=list)


class CreatePostRequest(BaseModel):
    """发帖请求"""
    topic: str = Field(..., max_length=200, description="帖子标题")
    content: str = Field(..., min_length=1, description="帖子内容")
    group_id: Optional[int] = Field(default=None, description="所属小组ID（可选）")


class CommentItem(BaseModel):
    """评论信息"""
    id: int
    user_id: int
    username: str = ""
    content: str
    created_at: str = ""


class CommentListResponse(BaseModel):
    """评论列表"""
    comments: List[CommentItem] = Field(default_factory=list)


class CreateCommentRequest(BaseModel):
    """发表评论"""
    content: str = Field(..., min_length=1, description="评论内容")


class LikeResponse(BaseModel):
    """点赞结果"""
    liked: bool
    likes_count: int


# ============================================================
# 学习小组
# ============================================================

class GroupItem(BaseModel):
    """小组信息"""
    id: int
    name: str
    description: str = ""
    level: str
    schedule: str
    tags: List[str] = Field(default_factory=list)
    member_count: int = 0
    is_joined: bool = False
    created_at: str = ""


class GroupListResponse(BaseModel):
    """小组列表"""
    groups: List[GroupItem] = Field(default_factory=list)


class JoinResult(BaseModel):
    """加入/退出结果"""
    joined: bool
    member_count: int


class CreateGroupRequest(BaseModel):
    """创建小组请求"""
    name: str = Field(..., min_length=1, max_length=100, description="小组名称")
    description: str = Field(default="", max_length=500, description="小组简介")
    level: str = Field(default="A1", description="等级范围，如 A1-B1")
    schedule: str = Field(default="", description="活动时间")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    max_members: int = Field(default=20, ge=2, le=100, description="最大人数")


class GroupMemberItem(BaseModel):
    """小组成员信息"""
    user_id: int
    username: str
    avatar: str = ""
    role: str = "member"
    joined_at: str = ""


class GroupDetailResponse(BaseModel):
    """小组详情"""
    id: int
    name: str
    description: str = ""
    level: str
    schedule: str
    tags: List[str] = Field(default_factory=list)
    member_count: int = 0
    max_members: int = 20
    is_joined: bool = False
    created_at: str = ""
    members: List[GroupMemberItem] = Field(default_factory=list)