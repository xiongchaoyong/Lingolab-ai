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

