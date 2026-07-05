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
    name: str = Field(..., max_length=50)
    description: str = Field(default="", max_length=200)
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
    class_id: Optional[int] = None
    class_ids: Optional[List[int]] = None
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


class UserRoleRequest(BaseModel):
    """修改用户角色"""
    role: str = Field(..., pattern="^(learner|teacher|admin)$")


class UpdateClassRequest(BaseModel):
    """编辑班级"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    level_range: Optional[str] = Field(default=None)


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
    daily_new_users: int = 0
    total_duration_minutes: int = 0
    avg_duration_minutes: float = 0.0
    conversation_completion_rate: float = 0.0
    teacher_count: int = 0
    learner_count: int = 0
    total_classes: int = 0
    avg_students_per_class: float = 0.0
    today_tasks_completed: int = 0
    today_pronunciation: int = 0
    today_conversations: int = 0
    task_completion_rate: float = 0.0
    total_points: int = 0


class ContentRankItem(BaseModel):
    """内容使用排行条目"""
    name: str
    type: str = ""
    count: int = 0


class ConversionFunnel(BaseModel):
    """转化漏斗数据"""
    registered: int = 0
    assessed: int = 0
    first_practice: int = 0
    retained_7d: int = 0


class DailyReportItem(BaseModel):
    """每日活跃日报条目"""
    date: str
    dau: int = 0
    new_users: int = 0
    practice_count: int = 0
    conversation_count: int = 0
    tasks_completed: int = 0


class TrendLabel(BaseModel):
    """仪表盘趋势标签（label/value 结构）"""
    label: str = ""
    value: int = 0


class DashboardResponse(BaseModel):
    """仪表盘完整数据"""
    metrics: DashboardMetrics
    user_trend: List[TrendLabel] = Field(default_factory=list)
    daily_activity: List[TrendLabel] = Field(default_factory=list)
    content_type_distribution: dict = Field(default_factory=dict)
    level_distribution: dict = Field(default_factory=dict)
    content_ranking: List[ContentRankItem] = Field(default_factory=list)
    conversion_funnel: ConversionFunnel = Field(default_factory=ConversionFunnel)
    daily_report: List[DailyReportItem] = Field(default_factory=list)


# ============================================================
# 教师工作台 Dashboard
# ============================================================

class TeacherDashboardResponse(BaseModel):
    """教师端仪表盘"""
    total_classes: int = 0
    total_students: int = 0
    pending_reviews: int = 0
    total_assignments: int = 0
    active_students_today: int = 0
    avg_class_size: float = 0.0
    recent_assignments: List[AssignmentItem] = Field(default_factory=list)
    class_student_counts: List[dict] = Field(default_factory=list)


# ============================================================
# 学生进度趋势
# ============================================================

class TrendDataPoint(BaseModel):
    """趋势数据点（四维度）"""
    date: str
    pronunciation: float = 0
    fluency: float = 0
    grammar: float = 0
    vocabulary: float = 0


class StudentTrendResponse(BaseModel):
    """学生趋势数据"""
    trend: List[TrendDataPoint] = Field(default_factory=list)


# ============================================================
# 学习打卡统计
# ============================================================

class CheckinDay(BaseModel):
    """单日打卡"""
    date: str
    completed: int = 0
    total: int = 0


class CheckinStatsResponse(BaseModel):
    """打卡统计"""
    checkins: List[CheckinDay] = Field(default_factory=list)
    streak: int = 0
    total_days: int = 0
    completion_rate: float = 0.0


# ============================================================
# 反馈管理
# ============================================================

class FeedbackItem(BaseModel):
    """反馈条目"""
    id: int
    user_id: int
    username: str = ""
    content: str
    feedback_type: str = "other"
    status: str = "pending"
    admin_reply: Optional[str] = None
    replied_at: Optional[str] = None
    created_at: str = ""


class FeedbackListResponse(BaseModel):
    """反馈列表"""
    feedbacks: List[FeedbackItem] = Field(default_factory=list)
    total: int = 0


class CreateFeedbackRequest(BaseModel):
    """用户提交反馈"""
    content: str = Field(..., min_length=1, max_length=2000, description="反馈内容")
    feedback_type: str = Field(default="other", pattern="^(bug|feature|scene|other)$", description="反馈类型")


class FeedbackReplyRequest(BaseModel):
    """回复反馈"""
    reply: str = Field(..., min_length=1)


class FeedbackStatusRequest(BaseModel):
    """修改反馈状态"""
    status: str = Field(..., pattern="^(pending|resolved)$")


# ============================================================
# 内容管理 CRUD
# ============================================================

class ContentCreateRequest(BaseModel):
    """通用内容创建"""
    content_type: str = Field(..., description="questions/shadow/materials/dubbing")
    data: dict = Field(..., description="内容数据（根据类型不同字段不同）")


class ContentUpdateRequest(BaseModel):
    """通用内容更新"""
    content_type: str = Field(..., description="questions/shadow/materials/dubbing")
    data: dict = Field(..., description="更新的字段")


# ============================================================
# 知识库管理
# ============================================================

class KnowledgeDocItem(BaseModel):
    """知识库文档条目"""
    id: int
    title: str
    content: str = ""
    category: str = "general"
    source_type: str = "manual"
    is_active: int = 1
    created_at: str = ""
    updated_at: str = ""


class KnowledgeDocListResponse(BaseModel):
    """知识库文档列表"""
    items: List[KnowledgeDocItem] = Field(default_factory=list)
    total: int = 0


class KnowledgeDocCreateRequest(BaseModel):
    """新增知识库文档"""
    title: str = Field(..., max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field(default="general", pattern="^(product_use|study_advice|tech_issue|refund|general)$")


class KnowledgeDocUpdateRequest(BaseModel):
    """更新知识库文档"""
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = None
    category: Optional[str] = Field(default=None, pattern="^(product_use|study_advice|tech_issue|refund|general)$")
    is_active: Optional[int] = Field(default=None, ge=0, le=1)


class SearchLogItem(BaseModel):
    """检索日志条目"""
    id: int
    user_id: Optional[int] = None
    username: str = ""
    query: str
    retrieved_docs: Optional[list] = None
    reply: Optional[str] = None
    created_at: str = ""


class SearchLogListResponse(BaseModel):
    """检索日志列表"""
    items: List[SearchLogItem] = Field(default_factory=list)
    total: int = 0