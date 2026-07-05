"""用户反馈 API — 用户端提交反馈"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.admin import CreateFeedbackRequest, FeedbackItem
from app.services.admin import admin_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=FeedbackItem)
async def submit_feedback(
    body: CreateFeedbackRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户提交反馈"""
    result = admin_service.submit_feedback(
        current_user.id, body.content, body.feedback_type, db
    )
    db.commit()
    return FeedbackItem(**result)
