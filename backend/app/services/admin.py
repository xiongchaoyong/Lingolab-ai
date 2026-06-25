"""后台管理服务 — 教师端班级+作业 / 运营端用户+仪表盘"""

import logging
import secrets
from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission, AdminLog
from app.models.user import UserProfile
from app.models.profile import UserSkillScore

logger = logging.getLogger(__name__)


class TeacherService:
    """教师端服务"""

    # ===== 班级管理 =====

    def get_my_classes(self, teacher_id: int, db: Session) -> List[Dict]:
        """获取我的班级列表"""
        classes = (
            db.query(Class)
            .filter(Class.teacher_id == teacher_id, Class.is_active == 1)
            .order_by(Class.created_at.desc())
            .all()
        )
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description or "",
                "level_range": c.level_range or "",
                "student_count": c.student_count,
                "invite_code": c.invite_code,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else "",
            }
            for c in classes
        ]

    def create_class(self, teacher_id: int, name: str, description: str, level_range: str, db: Session) -> Dict:
        """创建班级"""
        invite_code = "LINGO-" + secrets.token_hex(3).upper()
        cls = Class(
            name=name,
            description=description,
            teacher_id=teacher_id,
            invite_code=invite_code,
            level_range=level_range,
        )
        db.add(cls)
        db.flush()
        return {
            "id": cls.id, "name": cls.name, "description": cls.description or "",
            "level_range": cls.level_range or "", "student_count": 0,
            "invite_code": cls.invite_code, "is_active": cls.is_active,
            "created_at": cls.created_at.isoformat() if cls.created_at else "",
        }

    def get_students(self, class_id: int, teacher_id: int, db: Session) -> List[Dict]:
        """获取班级学生列表"""
        cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")

        members = (
            db.query(ClassStudent, UserProfile)
            .join(UserProfile, ClassStudent.user_id == UserProfile.id)
            .filter(ClassStudent.class_id == class_id)
            .all()
        )
        result = []
        for cs, user in members:
            # 计算学习总时长
            total_minutes = (
                db.query(func.count(UserSkillScore.id))
                .filter(UserSkillScore.user_id == user.id)
                .scalar()
            ) or 0
            result.append({
                "id": user.id,
                "username": user.username,
                "level_final": user.level_final,
                "total_minutes": total_minutes,
                "joined_at": cs.joined_at.isoformat() if cs.joined_at else "",
            })
        return result

    def join_class(self, user_id: int, invite_code: str, db: Session) -> Dict:
        """学生通过邀请码加入班级"""
        cls = db.query(Class).filter(Class.invite_code == invite_code, Class.is_active == 1).first()
        if not cls:
            raise ValueError("邀请码无效")

        existing = (
            db.query(ClassStudent)
            .filter(ClassStudent.class_id == cls.id, ClassStudent.user_id == user_id)
            .first()
        )
        if existing:
            raise ValueError("你已在该班级中")

        db.add(ClassStudent(class_id=cls.id, user_id=user_id))
        cls.student_count += 1
        db.flush()
        return {"class_id": cls.id, "class_name": cls.name, "joined": True}

    # ===== 作业管理 =====

    def get_assignments(self, teacher_id: int, db: Session) -> List[Dict]:
        """获取我的作业列表"""
        assignments = (
            db.query(Assignment)
            .join(Class, Assignment.class_id == Class.id)
            .filter(Class.teacher_id == teacher_id)
            .order_by(Assignment.created_at.desc())
            .all()
        )
        result = []
        for a in assignments:
            cls = db.query(Class).filter(Class.id == a.class_id).first()
            result.append({
                "id": a.id, "class_id": a.class_id,
                "class_name": cls.name if cls else "",
                "title": a.title, "description": a.description,
                "content_type": a.content_type,
                "content_ids": a.content_ids or [],
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "completion_rate": float(a.completion_rate) if a.completion_rate else 0.0,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            })
        return result

    def create_assignment(self, teacher_id: int, data: Dict, db: Session) -> Dict:
        """布置作业"""
        cls = db.query(Class).filter(Class.id == data["class_id"], Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")

        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])

        assignment = Assignment(
            class_id=data["class_id"],
            title=data["title"],
            description=data.get("description", ""),
            content_type=data["content_type"],
            content_ids=data.get("content_ids", []),
            due_date=due_date,
        )
        db.add(assignment)
        db.flush()
        return {
            "id": assignment.id, "class_id": assignment.class_id,
            "class_name": cls.name,
            "title": assignment.title, "description": assignment.description,
            "content_type": assignment.content_type,
            "content_ids": assignment.content_ids or [],
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "completion_rate": 0.0,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else "",
        }

    def get_submissions(self, assignment_id: int, teacher_id: int, db: Session) -> List[Dict]:
        """获取作业提交列表"""
        assignment = (
            db.query(Assignment)
            .join(Class, Assignment.class_id == Class.id)
            .filter(Assignment.id == assignment_id, Class.teacher_id == teacher_id)
            .first()
        )
        if not assignment:
            raise ValueError("作业不存在")

        subs = (
            db.query(AssignmentSubmission)
            .filter(AssignmentSubmission.assignment_id == assignment_id)
            .order_by(AssignmentSubmission.submitted_at.desc())
            .all()
        )
        result = []
        for s in subs:
            user = db.query(UserProfile).filter(UserProfile.id == s.user_id).first()
            result.append({
                "id": s.id, "user_id": s.user_id,
                "username": user.username if user else "未知",
                "assignment_id": s.assignment_id,
                "audio_url": s.audio_url,
                "score": float(s.score) if s.score else None,
                "teacher_feedback": s.teacher_feedback,
                "teacher_score": float(s.teacher_score) if s.teacher_score else None,
                "status": s.status,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else "",
            })
        return result

    def review_submission(self, submission_id: int, teacher_id: int, feedback: str, score: float | None, db: Session) -> Dict:
        """教师点评作业"""
        sub = (
            db.query(AssignmentSubmission)
            .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
            .join(Class, Assignment.class_id == Class.id)
            .filter(AssignmentSubmission.id == submission_id, Class.teacher_id == teacher_id)
            .first()
        )
        if not sub:
            raise ValueError("提交记录不存在")

        sub.teacher_feedback = feedback
        sub.teacher_score = score
        sub.status = "reviewed"
        db.flush()

        user = db.query(UserProfile).filter(UserProfile.id == sub.user_id).first()
        return {
            "id": sub.id, "user_id": sub.user_id,
            "username": user.username if user else "未知", "assignment_id": sub.assignment_id,
            "audio_url": sub.audio_url,
            "score": float(sub.score) if sub.score else None,
            "teacher_feedback": sub.teacher_feedback,
            "teacher_score": float(sub.teacher_score) if sub.teacher_score else None,
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else "",
        }


class AdminService:
    """运营端服务"""

    def get_users(self, page: int, page_size: int, search: str, role: str, db: Session) -> Dict:
        """获取用户列表（分页+搜索+筛选）"""
        query = db.query(UserProfile)

        if search:
            query = query.filter(UserProfile.username.contains(search))
        if role:
            query = query.filter(UserProfile.role == role)

        total = query.count()
        users = query.order_by(UserProfile.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for u in users:
            total_minutes = (
                db.query(func.count(UserSkillScore.id))
                .filter(UserSkillScore.user_id == u.id)
                .scalar()
            ) or 0
            items.append({
                "id": u.id, "username": u.username,
                "role": u.role, "level_final": u.level_final,
                "total_minutes": total_minutes,
                "is_active": u.is_active,
                "assessment_completed": u.assessment_completed,
                "created_at": u.created_at.isoformat() if u.created_at else "",
            })

        return {"users": items, "total": total}

    def set_user_status(self, user_id: int, is_active: int, admin_id: int, db: Session) -> Dict:
        """启用/禁用用户"""
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        old_status = user.is_active
        user.is_active = is_active
        db.flush()

        # 记录操作日志
        db.add(AdminLog(
            admin_id=admin_id,
            action="user_disable" if is_active == 0 else "user_enable",
            target_type="user",
            target_id=user_id,
            detail=f"用户状态 {old_status} → {is_active}",
        ))
        db.flush()
        return {"id": user.id, "is_active": user.is_active}

    def get_dashboard(self, db: Session) -> Dict:
        """获取运营仪表盘数据"""
        today = date.today()

        # 总用户数
        total_users = db.query(func.count(UserProfile.id)).scalar() or 0
        active_users = db.query(func.count(UserProfile.id)).filter(UserProfile.is_active == 1).scalar() or 0

        # DAU — 今日活跃用户
        dau = (
            db.query(func.count(func.distinct(UserSkillScore.user_id)))
            .filter(func.date(UserSkillScore.created_at) == today)
            .scalar()
        ) or 0

        # MAU — 本月活跃用户
        month_start = today.replace(day=1)
        mau = (
            db.query(func.count(func.distinct(UserSkillScore.user_id)))
            .filter(func.date(UserSkillScore.created_at) >= month_start)
            .scalar()
        ) or 0

        # 用户增长趋势（最近6个月）
        user_trend = []
        for i in range(5, -1, -1):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1)
            else:
                month_end = date(year, month + 1, 1)
            count = (
                db.query(func.count(UserProfile.id))
                .filter(UserProfile.created_at >= month_start, UserProfile.created_at < month_end)
                .scalar()
            ) or 0
            user_trend.append({"label": f"{month}月", "value": count})

        # 内容类型分布
        type_dist = dict(
            db.query(UserSkillScore.dimension, func.count(UserSkillScore.id))
            .group_by(UserSkillScore.dimension)
            .all()
        )

        # 等级分布
        level_dist = dict(
            db.query(UserProfile.level_final, func.count(UserProfile.id))
            .filter(UserProfile.level_final.isnot(None))
            .group_by(UserProfile.level_final)
            .all()
        )

        return {
            "metrics": {
                "dau": dau,
                "mau": mau,
                "retention_d1": 0.0,
                "retention_d7": 0.0,
                "total_users": total_users,
                "active_users": active_users,
            },
            "user_trend": user_trend,
            "content_type_distribution": type_dist,
            "level_distribution": level_dist,
        }


# 单例
teacher_service = TeacherService()
admin_service = AdminService()