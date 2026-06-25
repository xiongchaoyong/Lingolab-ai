"""游戏化闯关 — 请求/响应 Schema"""

from typing import List, Optional
from datetime import date, datetime

from pydantic import BaseModel, Field


# ============================================================
# 每日闯关
# ============================================================

class ChallengeLevelItem(BaseModel):
    """单个关卡内容"""
    level: int = Field(..., description="关卡序号 1-5")
    text: str = Field(..., description="跟读文本")
    difficulty: str = Field(..., description="CEFR 难度等级 A1/B1/B2")
    pass_score: int = Field(default=70, description="通过分数")


class DailyChallengeResponse(BaseModel):
    """每日闯关响应"""
    levels: List[ChallengeLevelItem] = Field(..., description="5个关卡内容")
    date: str = Field(..., description="挑战日期 YYYY-MM-DD")
    completed: bool = Field(default=False, description="是否已全部完成")
    current_level: int = Field(default=1, description="当前所在关卡")
    level_scores: dict = Field(default_factory=dict, description="已完成的关卡分数 {level: score}")


class SubmitLevelRequest(BaseModel):
    """提交关卡请求（通过 FormData 上传音频，此处仅文本字段）"""
    level: int = Field(..., ge=1, le=5, description="关卡序号")


class SubmitLevelResponse(BaseModel):
    """单关评分结果"""
    level: int = Field(..., description="关卡序号")
    score: float = Field(..., description="发音得分 0-100")
    passed: bool = Field(..., description="是否通过（≥70）")
    dimensions: dict = Field(default_factory=dict, description="五维评分明细")


class CompleteChallengeResponse(BaseModel):
    """闯关完成响应"""
    levels_passed: int = Field(..., description="通过的关卡数")
    points_earned: int = Field(..., description="本次获得积分")
    total_points: int = Field(..., description="累计总积分")
    new_badges: List["BadgeItem"] = Field(default_factory=list, description="新获得的勋章")


# ============================================================
# 配音挑战
# ============================================================

class DubbingContentItem(BaseModel):
    """配音内容"""
    id: int = Field(..., description="内容ID")
    title: str = Field(..., description="片段标题")
    source: str = Field(default="", description="来源")
    difficulty: str = Field(..., description="难度 easy/medium/hard")
    duration: int = Field(..., description="时长（秒）")
    subtitle: str = Field(..., description="字幕文本")


class DubbingScoreResponse(BaseModel):
    """配音评分结果"""
    content_id: int = Field(..., description="配音内容ID")
    pronunciation_score: float = Field(..., description="发音相似度 0-100")
    intonation_score: float = Field(..., description="语调相似度 0-100")
    emotion_score: float = Field(..., description="情感匹配度 0-100")
    total_score: float = Field(..., description="综合评分 0-100")
    points_earned: int = Field(..., description="本次获得积分")


class DubbingRecordItem(BaseModel):
    """配音历史记录"""
    id: int = Field(..., description="记录ID")
    content_title: str = Field(..., description="片段标题")
    total_score: Optional[float] = Field(default=None, description="综合评分")
    created_at: datetime = Field(..., description="配音时间")


# ============================================================
# 积分 & 勋章
# ============================================================

class BadgeItem(BaseModel):
    """勋章"""
    badge_type: str = Field(..., description="勋章类型标识")
    badge_name: str = Field(..., description="勋章名称")
    description: str = Field(default="", description="勋章描述")
    earned: bool = Field(default=False, description="是否已获得")
    awarded_at: Optional[datetime] = Field(default=None, description="获得时间")


class PointsRecord(BaseModel):
    """积分记录"""
    id: int = Field(..., description="记录ID")
    action_type: str = Field(..., description="行为类型")
    score: int = Field(..., description="积分变化值")
    description: str = Field(default="", description="说明")
    created_at: datetime = Field(..., description="时间")


class PointsResponse(BaseModel):
    """积分总览"""
    total_points: int = Field(..., description="累计总积分")
    recent_records: List[PointsRecord] = Field(default_factory=list, description="最近积分记录")


# ============================================================
# 排行榜
# ============================================================

class LeaderboardItem(BaseModel):
    """排行榜条目"""
    rank: int = Field(..., description="排名")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    total_points: int = Field(..., description="总积分")
    badge_count: int = Field(default=0, description="勋章数量")