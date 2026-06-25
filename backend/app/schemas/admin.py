"""后台管理 — 请求/响应 Schema"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# 班级管理
# ============================================================

class ClassItem(BaseModel):
    """班级条目"""
    id: int
    name: str
    description: str = ""
    level_range: str = ""
    student_count: int = 0
    invite_code: str = ""
    is_active: int = 1
    created_at: str = ""


class ClassListResponse(BaseModel):
    """班级列表"""
    classes: List[ClassItem] = Field(default_factory=list)


class CreateClassRequest(BaseModel):
    """创建班级"""
    name: str = Field(..., max_length=100)
    description: str = ""
    level_range: str = ""


class JoinClassRequest(BaseModel):
    """加入班级"""
    invite_code: str = Field(..., min_length=1)


class StudentItem(BaseModel):
    """学生信息"""
    id: int
    username: str
    level_final: Optional[str] = None
    total_minutes: int = 0
    joined_at: str = ""


class StudentListResponse(BaseModel):
    """学生列表"""
    students: List[StudentItem] = Field(default_factory=list)


# ============================================================
# 作业管理
# ============================================================

class AssignmentItem(BaseModel):
    """作业条目"""
    id: int
    class_id: int
    class_name: str = ""
    title: str
    description: Optional[str] = None
    content_type: str
    content_ids: list = Field(default_factory=list)
    due_date: Optional[str] = None
    completion_rate: float = 0.0
    created_at: str = ""


class AssignmentListResponse(BaseModel):
    """作业列表"""
    assignments: List[AssignmentItem] = Field(default_factory=list)


class CreateAssignmentRequest(BaseModel):
    """布置作业"""
    class_id: int
    title: str = Field(..., max_length=200)
    description: str = ""
    content_type: str = Field(..., description="pronunciation/conversation/dubbing")
    content_ids: List[int] = Field(default_factory=list)
    due_date: Optional[str] = None


class SubmissionItem(BaseModel):
    """作业提交"""
    id: int
    user_id: int
    username: str = ""
    assignment_id: int
    audio_url: Optional[str] = None
    score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    teacher_score: Optional[float] = None
    status: str = "submitted"
    submitted_at: str = ""


class SubmissionListResponse(BaseModel):
    """提交列表"""
    submissions: List[SubmissionItem] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    """教师点评"""
    teacher_feedback: str = ""
    teacher_score: Optional[float] = Field(default=None, ge=0, le=100)


# ============================================================
# 运营管理
# ============================================================

class UserListItem(BaseModel):
    """用户列表条目"""
    id: int
    username: str
    role: str
    level_final: Optional[str] = None
    total_minutes: int = 0
    is_active: int = 1
    assessment_completed: int = 0
    created_at: str = ""


class UserListResponse(BaseModel):
    """用户列表"""
    users: List[UserListItem] = Field(default_factory=list)
    total: int = 0


class UserStatusRequest(BaseModel):
    """修改用户状态"""
    is_active: int = Field(..., ge=0, le=1)


# ============================================================
# 数据仪表盘
# ============================================================

class DashboardMetrics(BaseModel):
    """仪表盘核心指标"""
    dau: int = 0
    mau: int = 0
    retention_d1: float = 0.0
    retention_d7: float = 0.0
    total_users: int = 0
    active_users: int = 0


class TrendPoint(BaseModel):
    """趋势数据点"""
    label: str
    value: int


class DashboardResponse(BaseModel):
    """仪表盘完整数据"""
    metrics: DashboardMetrics
    user_trend: List[TrendPoint] = Field(default_factory=list)
    content_type_distribution: dict = Field(default_factory=dict)
    level_distribution: dict = Field(default_factory=dict)