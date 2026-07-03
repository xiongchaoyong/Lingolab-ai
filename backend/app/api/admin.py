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
    UserRoleRequest,
    UpdateClassRequest,
    DashboardResponse,
    FeedbackListResponse,
    FeedbackReplyRequest,
    FeedbackStatusRequest,
    ContentCreateRequest,
    ContentUpdateRequest,
    KnowledgeDocListResponse,
    KnowledgeDocCreateRequest,
    KnowledgeDocUpdateRequest,
    SearchLogListResponse,
)
from app.services.admin import teacher_service, admin_service

router = APIRouter()
logger = logging.getLogger(__name__)


def require_teacher(current_user: UserProfile = Depends(get_current_user)):
    """要求教师或管理员角色"""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="仅教师或管理员可访问")
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


@router.post("/classes/{class_id}/refresh-code", response_model=dict)
def refresh_invite_code(
    class_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """刷新班级邀请码"""
    try:
        result = teacher_service.refresh_invite_code(class_id, teacher.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "邀请码已刷新"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/classes/{class_id}", response_model=dict)
def update_class(
    class_id: int,
    req: UpdateClassRequest,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """编辑班级信息"""
    try:
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        if not data:
            raise HTTPException(status_code=400, detail="至少提供一个更新字段")
        result = teacher_service.update_class(class_id, teacher.id, data, db)
        db.commit()
        return {"code": 0, "data": result, "message": "更新成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/classes/{class_id}", response_model=dict)
def delete_class(
    class_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """删除班级（软删除）"""
    try:
        result = teacher_service.delete_class(class_id, teacher.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "班级已删除"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/classes/{class_id}/students/{user_id}", response_model=dict)
def remove_student_from_class(
    class_id: int,
    user_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """从班级移除学生"""
    try:
        result = teacher_service.remove_student(class_id, user_id, teacher.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "学生已移除"}
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


@router.put("/users/{user_id}/role", response_model=dict)
def set_user_role(
    user_id: int,
    req: UserRoleRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """修改用户角色（learner/teacher/admin）"""
    try:
        result = admin_service.set_user_role(user_id, req.role, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": f"角色已更新为 {req.role}"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=dict)
def get_user_detail(
    user_id: int,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取用户详细信息"""
    try:
        return admin_service.get_user_detail(user_id, db)
    except ValueError as e:
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


# ============================================================
# 教师端 — 学生报告
# ============================================================

@router.get("/students")
def get_all_students(
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取教师所有班级的学生列表"""
    students = teacher_service.get_all_students(teacher.id, db)
    return {"students": students}


@router.get("/students/{student_id}")
def get_student_detail(
    student_id: int,
    teacher: UserProfile = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """获取学生详细报告"""
    try:
        result = teacher_service.get_student_detail(student_id, teacher.id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 运营端 — 内容管理
# ============================================================

@router.get("/content/{content_type}")
def get_content_list(
    content_type: str,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取内容列表（questions/shadow/materials/dubbing）"""
    if content_type not in ("questions", "shadow", "materials", "dubbing"):
        raise HTTPException(status_code=400, detail="无效的内容类型")
    items = admin_service.get_content_list(content_type, db)
    return {"items": items}


@router.post("/content", response_model=dict)
def create_content(
    req: ContentCreateRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建内容项"""
    try:
        result = admin_service.create_content(req.content_type, req.data, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "创建成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/content/{content_type}/{item_id}", response_model=dict)
def update_content(
    content_type: str,
    item_id: int,
    req: ContentUpdateRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """更新内容项"""
    try:
        result = admin_service.update_content(content_type, item_id, req.data, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "更新成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/content/{content_type}/{item_id}", response_model=dict)
def delete_content(
    content_type: str,
    item_id: int,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除内容项（软删除）"""
    try:
        result = admin_service.delete_content(content_type, item_id, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "删除成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 运营端 — 反馈管理
# ============================================================

@router.get("/feedbacks", response_model=FeedbackListResponse)
def get_feedbacks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取反馈列表（分页+状态筛选）"""
    result = admin_service.get_feedbacks(page, page_size, status, db)
    return FeedbackListResponse(**result)


@router.post("/feedbacks/{feedback_id}/reply", response_model=dict)
def reply_feedback(
    feedback_id: int,
    req: FeedbackReplyRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """回复反馈"""
    try:
        result = admin_service.reply_feedback(feedback_id, req.reply, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "回复成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/feedbacks/{feedback_id}/resolve", response_model=dict)
def resolve_feedback(
    feedback_id: int,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """标记反馈为已解决"""
    try:
        result = admin_service.resolve_feedback(feedback_id, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "已标记解决"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# 运营端 — 知识库管理
# ============================================================

@router.get("/knowledge", response_model=KnowledgeDocListResponse)
def get_knowledge_docs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    category: str = Query(""),
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取知识库文档列表（分页+搜索+分类）"""
    result = admin_service.get_knowledge_docs(page, page_size, search, category, db)
    return KnowledgeDocListResponse(**result)


@router.post("/knowledge", response_model=dict)
def create_knowledge_doc(
    req: KnowledgeDocCreateRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """新增知识库文档"""
    try:
        result = admin_service.create_knowledge_doc(req.model_dump(), admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "创建成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/knowledge/{doc_id}", response_model=dict)
def update_knowledge_doc(
    doc_id: int,
    req: KnowledgeDocUpdateRequest,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """编辑知识库文档"""
    try:
        # 只传有值的字段
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        if not data:
            raise HTTPException(status_code=400, detail="至少提供一个更新字段")
        result = admin_service.update_knowledge_doc(doc_id, data, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "更新成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/knowledge/{doc_id}", response_model=dict)
def delete_knowledge_doc(
    doc_id: int,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除知识库文档（软删除）"""
    try:
        result = admin_service.delete_knowledge_doc(doc_id, admin.id, db)
        db.commit()
        return {"code": 0, "data": result, "message": "删除成功"}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/knowledge/{doc_id}/reindex", response_model=dict)
def reindex_knowledge_doc(
    doc_id: int,
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """重新索引单条文档"""
    try:
        result = admin_service.reindex_document(doc_id, db)
        return {"code": 0, "data": result, "message": result.get("message", "")}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/knowledge/rebuild-index", response_model=dict)
def rebuild_knowledge_index(
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """全量重建向量索引"""
    result = admin_service.rebuild_index(db)
    return {"code": 0, "data": result, "message": result.get("message", "")}


@router.get("/knowledge/logs", response_model=SearchLogListResponse)
def get_search_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Query(None),
    admin: UserProfile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取检索日志列表（分页）"""
    result = admin_service.get_search_logs(page, page_size, user_id, db)
    return SearchLogListResponse(**result)