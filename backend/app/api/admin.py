"""后台管理 API 路由 — 教师端班级+作业 / 运营端用户+仪表盘"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.admin import (
    ClassListResponse,
    CreateClassRequest,
    StudentListResponse,
    JoinClassRequest,
    AssignmentListResponse,
    CreateAssignmentRequest,
    SubmissionListResponse,
    ReviewRequest,
    UserListResponse,
    UserStatusRequest,
    DashboardResponse,
)
from app.services.admin import teacher_service, admin_service

router = APIRouter()
logger = logging.getLogger(__name__)


def require_teacher(current_user: UserProfile = Depends(get_current_user)):
    """要求教师角色"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="仅教师可访问")
    return current_user


def require_admin(current_user: UserProfile = Depends(get_current_user)):
    """要求管理员角色"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return current_user


# ============================================================
# 教师端 — 班级管理
# ============================================================

@router.get("/classes", response_model=ClassListResponse)
def get_my_classes(
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取我的班级列表"""
    classes = teacher_service.get_my_classes(teacher.id, db)
    return ClassListResponse(classes=classes)


@router.post("/classes", response_model=dict)
def create_class(
    req: CreateClassRequest,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """创建班级"""
    try:
        result = teacher_service.create_class(
            teacher.id, req.name, req.description, req.level_range, db
        )
        db.commit()
        return {"code": 0, "data": result, "message": "创建成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/classes/{class_id}/students", response_model=StudentListResponse)
def get_class_students(
    class_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取班级学生列表"""
    try:
        students = teacher_service.get_students(class_id, teacher.id, db)
        return StudentListResponse(students=students)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/classes/join", response_model=dict)
def join_class(
    req: JoinClassRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """学生通过邀请码加入班级"""
    try:
        result = teacher_service.join_class(current_user.id, req.invite_code, db)
        db.commit()
        return {"code": 0, "data": result, "message": "加入成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 教师端 — 作业管理
# ============================================================

@router.get("/assignments", response_model=AssignmentListResponse)
def get_assignments(
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取我的作业列表"""
    assignments = teacher_service.get_assignments(teacher.id, db)
    return AssignmentListResponse(assignments=assignments)


@router.post("/assignments", response_model=dict)
def create_assignment(
    req: CreateAssignmentRequest,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """布置作业"""
    try:
        result = teacher_service.create_assignment(teacher.id, req.model_dump(), db)
        db.commit()
        return {"code": 0, "data": result, "message": "布置成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assignments/{assignment_id}/submissions", response_model=SubmissionListResponse)
def get_submissions(
    assignment_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取作业提交列表"""
    try:
        submissions = teacher_service.get_submissions(assignment_id, teacher.id, db)
        return SubmissionListResponse(submissions=submissions)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/submissions/{submission_id}/review", response_model=dict)
def review_submission(
    submission_id: int,
    req: ReviewRequest,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """教师点评作业"""
    try:
        result = teacher_service.review_submission(
            submission_id, teacher.id, req.teacher_feedback, req.teacher_score, db
        )
        db.commit()
        return {"code": 0, "data": result, "message": "点评成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 运营端 — 用户管理
# ============================================================

@router.get("/users", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    role: str = Query(""),
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取用户列表（分页+搜索+筛选）"""
    result = admin_service.get_users(page, page_size, search, role, db)
    return UserListResponse(**result)


@router.put("/users/{user_id}/status", response_model=dict)
def set_user_status(
    user_id: int,
    req: UserStatusRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """启用/禁用用户"""
    try:
        result = admin_service.set_user_status(user_id, req.is_active, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "操作成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 运营端 — 数据仪表盘
# ============================================================

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取运营仪表盘数据"""
    result = admin_service.get_dashboard(db)
    return DashboardResponse(**result)