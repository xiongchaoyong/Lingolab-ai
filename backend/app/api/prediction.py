"""学习预测与通知 API 路由"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.prediction import (
    PredictionData,
    TargetScoreRequest,
    AlertCheckResponse,
    AlertItem,
    NoticesResponse,
    NoticeItem,
    UnreadCountResponse,
)
from app.services.prediction import prediction_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 学习预测
# ============================================================

@router.get("/prediction/current", response_model=PredictionData)
async def get_prediction(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前学习预测"""
    result = prediction_service.calculate_prediction(current_user.id, db)
    db.commit()
    return PredictionData(**result)


@router.put("/prediction/target", response_model=PredictionData)
async def set_target_score(
    body: TargetScoreRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """设置目标分数"""
    from app.models.gamification import LearningPrediction

    pred = (
        db.query(LearningPrediction)
        .filter(LearningPrediction.user_id == current_user.id)
        .first()
    )
    if pred:
        pred.target_score = body.target_score
    else:
        pred = LearningPrediction(
            user_id=current_user.id,
            current_score=0,
            target_score=body.target_score,
        )
        db.add(pred)
    db.commit()

    # 重新计算
    result = prediction_service.calculate_prediction(current_user.id, db)
    db.commit()
    return PredictionData(**result)


# ============================================================
# 预警
# ============================================================

@router.get("/prediction/alerts", response_model=AlertCheckResponse)
async def check_alerts(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查预警规则"""
    alerts = prediction_service.check_alerts(current_user.id, db)
    return AlertCheckResponse(alerts=[AlertItem(**a) for a in alerts])


# ============================================================
# 通知
# ============================================================

@router.get("/notices", response_model=NoticesResponse)
async def get_notices(
    unread_only: bool = Query(default=False, description="是否仅未读"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取通知列表"""
    items, unread_count = prediction_service.get_notices(
        current_user.id, db, unread_only
    )
    return NoticesResponse(
        notices=[NoticeItem(**i) for i in items],
        unread_count=unread_count,
    )


@router.put("/notices/{notice_id}/read")
async def mark_notice_read(
    notice_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单条通知已读"""
    success = prediction_service.mark_read(notice_id, current_user.id, db)
    if success:
        db.commit()
        return {"success": True}
    return {"success": False, "detail": "通知不存在"}


@router.put("/notices/read-all")
async def mark_all_notices_read(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记全部通知已读"""
    prediction_service.mark_all_read(current_user.id, db)
    db.commit()
    return {"success": True}


@router.get("/notices/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取未读通知数量"""
    count = prediction_service.get_unread_count(current_user.id, db)
    return UnreadCountResponse(unread_count=count)