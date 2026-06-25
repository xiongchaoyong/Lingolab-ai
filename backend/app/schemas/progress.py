"""学习进度可视化 — 请求/响应 Schema"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================
# 雷达图
# ============================================================

class RadarDimension(BaseModel):
    """雷达图单个维度"""
    name: str = Field(..., description="维度名称")
    current: float = Field(..., description="当前值 0-100")
    previous: float = Field(..., description="上次值 0-100")


class RadarResponse(BaseModel):
    """雷达图数据"""
    dimensions: List[RadarDimension] = Field(..., description="五维数据")
    range: str = Field(..., description="时间范围 day/week/month/all")


# ============================================================
# 趋势折线图
# ============================================================

class TrendPoint(BaseModel):
    """趋势图数据点"""
    date: str = Field(..., description="日期")
    pronunciation: float = Field(default=0, description="发音分")
    fluency: float = Field(default=0, description="流利度分")


class TrendResponse(BaseModel):
    """趋势图数据"""
    points: List[TrendPoint] = Field(..., description="数据点列表")
    range: str = Field(..., description="时间范围")


# ============================================================
# 日历热力图
# ============================================================

class HeatmapDay(BaseModel):
    """热力图单日数据"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    count: int = Field(default=0, description="活动次数")
    level: int = Field(default=0, description="颜色等级 0-3")


class HeatmapResponse(BaseModel):
    """热力图数据"""
    days: List[HeatmapDay] = Field(..., description="365天数据")
    year: int = Field(..., description="年份")


# ============================================================
# 统计卡片
# ============================================================

class StatCardItem(BaseModel):
    """统计卡片"""
    label: str = Field(..., description="指标名称")
    value: str = Field(..., description="指标值")
    unit: str = Field(default="", description="单位")


class StatsResponse(BaseModel):
    """统计数据"""
    stats: List[StatCardItem] = Field(..., description="6项核心统计")