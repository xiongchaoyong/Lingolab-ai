"""学习进度可视化 API 路由"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.progress import (
    RadarResponse,
    TrendResponse,
    HeatmapResponse,
    StatsResponse,
)
from app.services.progress import progress_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/radar", response_model=RadarResponse)
async def get_radar(
    range: str = Query(default="week", description="时间范围 day/week/month/all"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取雷达图五维能力数据"""
    if range not in ("day", "week", "month", "all"):
        range = "week"
    result = progress_service.get_radar_data(current_user.id, db, range)
    return RadarResponse(**result)


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    range: str = Query(default="week", description="时间范围 day/week/month/all"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取趋势折线图数据"""
    if range not in ("day", "week", "month", "all"):
        range = "week"
    result = progress_service.get_trend_data(current_user.id, db, range)
    return TrendResponse(**result)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    year: int = Query(default=None, description="年份，默认当前年"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取日历热力图数据"""
    if year is None:
        year = date.today().year
    result = progress_service.get_heatmap_data(current_user.id, db, year)
    return HeatmapResponse(**result)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取6项核心统计数据"""
    result = progress_service.get_stats(current_user.id, db)
    return StatsResponse(**result)