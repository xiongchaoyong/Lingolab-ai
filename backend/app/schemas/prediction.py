"""学习预测与预警 — 请求/响应 Schema"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# 学习预测
# ============================================================

class PredictionData(BaseModel):
    """学习预测数据"""
    current_score: float = Field(..., description="当前综合分 0-100")
    trend_slope: Optional[float] = Field(default=None, description="趋势斜率（分/天）")
    target_score: float = Field(..., description="目标分数")
    predicted_days: Optional[int] = Field(default=None, description="预计达标天数")
    predicted_date: Optional[str] = Field(default=None, description="预计达标日期")
    trend: str = Field(default="stable", description="趋势方向 up/down/stable")
    message: str = Field(default="", description="预测说明")


class TargetScoreRequest(BaseModel):
    """设置目标分数"""
    target_score: float = Field(..., ge=1, le=100, description="目标分数")


# ============================================================
# 预警
# ============================================================

class AlertItem(BaseModel):
    """预警条目"""
    type: str = Field(..., description="预警类型")
    title: str = Field(..., description="预警标题")
    message: str = Field(..., description="预警详情")
    level: str = Field(..., description="级别 info/warning")
    triggered: bool = Field(default=False, description="是否触发")


class AlertCheckResponse(BaseModel):
    """预警检查结果"""
    alerts: List[AlertItem] = Field(..., description="预警列表")


# ============================================================
# 通知
# ============================================================

class NoticeItem(BaseModel):
    """通知条目"""
    id: int = Field(..., description="通知ID")
    type: str = Field(..., description="类型 prediction/alert/achievement")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="内容")
    level: str = Field(..., description="级别 info/warning")
    is_read: bool = Field(default=False, description="是否已读")
    created_at: datetime = Field(..., description="创建时间")


class NoticesResponse(BaseModel):
    """通知列表"""
    notices: List[NoticeItem] = Field(default_factory=list, description="通知列表")
    unread_count: int = Field(default=0, description="未读数量")


class UnreadCountResponse(BaseModel):
    """未读通知数量"""
    unread_count: int = Field(default=0, description="未读数量")