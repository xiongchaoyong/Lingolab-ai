"""学生端 API 路由 — 我的班级 + 我的作业"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.services.student import student_service

router = APIRouter()
logger = logging.getLogger(__name__)


class SubmitAssignmentRequest(BaseModel):
    """提交作业请求"""
    audio_url: str = Field(..., description="录音文件 URL")


@router.get("/classes")
def get_my_classes(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我加入的班级列表"""
    classes = student_service.get_my_classes(current_user.id, db)
    return {"classes": classes}


@router.get("/assignments")
def get_my_assignments(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我的作业列表"""
    assignments = student_service.get_my_assignments(current_user.id, db)
    return {"assignments": assignments}


@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    req: SubmitAssignmentRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交作业"""
    try:
        result = student_service.submit_assignment(
            current_user.id, assignment_id, req.audio_url, db
        )
        db.commit()
        return {"code": 0, "data": result, "message": result.get("message", "提交成功")}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))