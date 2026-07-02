"""用户画像模块 — 动态分数相关 Schema"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class SkillScoreItem(BaseModel):
    """单条技能分数"""
    dimension: str
    skill_name: str
    score: float
    source: str
    created_at: str


class ProfileScoresResponse(BaseModel):
    """用户技能分数响应"""
    level_final: Optional[str] = None
    dimension_scores: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="各维度当前 EMA 分数，如 {pronunciation: 72.5, fluency: 68.3}"
    )
    recent_scores: List[SkillScoreItem] = Field(
        default_factory=list,
        description="最近 100 条分数记录"
    )


class ProfileRefreshResponse(BaseModel):
    """档案刷新响应"""
    level_final: Optional[str] = None
    dimension_scores: Dict[str, Optional[float]] = Field(default_factory=dict)
    message: str = "Profile refreshed"


class CompleteTaskRequest(BaseModel):
    """完成任务请求"""
    score: Optional[float] = Field(default=None, description="任务得分 0-100")
    duration_seconds: Optional[int] = Field(default=None, description="完成耗时（秒）")