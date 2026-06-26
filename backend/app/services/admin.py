"""后台管理服务 — 教师端班级+作业 / 运营端用户+仪表盘"""

import logging
import secrets
from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission, AdminLog, UserFeedback
from app.models.user import UserProfile
from app.models.profile import UserSkillScore
from app.models.assessment import AssessmentQuestion
from app.models.pronunciation import PronunciationContent
from app.models.learning import LearningMaterial
from app.models.gamification import DubbingContent

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

    # ===== 学生报告 =====

    def get_all_students(self, teacher_id: int, db: Session) -> List[Dict]:
        """获取教师所有班级的学生列表（含学习统计）"""
        # 获取教师所有班级 ID
        class_ids = [
            c.id for c in db.query(Class).filter(Class.teacher_id == teacher_id).all()
        ]
        if not class_ids:
            return []

        # 获取这些班级的所有学生
        user_ids = [
            cs.user_id for cs in db.query(ClassStudent)
            .filter(ClassStudent.class_id.in_(class_ids))
            .all()
        ]
        if not user_ids:
            return []

        users = db.query(UserProfile).filter(UserProfile.id.in_(user_ids)).all()
        result = []
        for u in users:
            # 学习记录数（近似学习时长）
            score_count = (
                db.query(func.count(UserSkillScore.id))
                .filter(UserSkillScore.user_id == u.id)
                .scalar()
            ) or 0

            # 最近一条记录时间
            last_score = (
                db.query(UserSkillScore)
                .filter(UserSkillScore.user_id == u.id)
                .order_by(UserSkillScore.created_at.desc())
                .first()
            )
            last_active = ""
            if last_score and last_score.created_at:
                delta = datetime.now() - last_score.created_at
                if delta.days == 0:
                    last_active = "今天"
                elif delta.days == 1:
                    last_active = "昨天"
                else:
                    last_active = f"{delta.days}天前"

            result.append({
                "id": u.id,
                "username": u.username,
                "level_final": u.level_final or "未测评",
                "total_minutes": score_count * 5,  # 粗略估算
                "streak": 0,  # 需要打卡表支持
                "last_active": last_active,
            })
        return result

    def get_student_detail(self, student_id: int, teacher_id: int, db: Session) -> Dict:
        """获取学生详细报告（维度分数 + 最近活动）"""
        user = db.query(UserProfile).filter(UserProfile.id == student_id).first()
        if not user:
            raise ValueError("学生不存在")

        # 验证师生关系
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == teacher_id).all()]
        if class_ids:
            is_student = (
                db.query(ClassStudent)
                .filter(ClassStudent.class_id.in_(class_ids), ClassStudent.user_id == student_id)
                .first()
            )
            if not is_student:
                raise ValueError("该学生不在你的班级中")

        # 获取维度分数
        dim_scores = {}
        recent_scores = (
            db.query(UserSkillScore)
            .filter(UserSkillScore.user_id == student_id)
            .order_by(UserSkillScore.created_at.desc())
            .limit(50)
            .all()
        )
        for s in recent_scores:
            dim = s.dimension
            if dim not in dim_scores:
                dim_scores[dim] = []
            dim_scores[dim].append(float(s.score))

        dimension_averages = {
            dim: round(sum(scores) / len(scores), 1)
            for dim, scores in dim_scores.items()
        } if dim_scores else {}

        # 最近活动
        recent_activities = []
        for s in recent_scores[:10]:
            recent_activities.append({
                "dimension": s.dimension,
                "score": float(s.score),
                "source_type": s.source_type,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            })

        return {
            "id": user.id,
            "username": user.username,
            "level_final": user.level_final or "未测评",
            "learning_goal": user.learning_goal,
            "age_group": user.age_group,
            "dimension_averages": dimension_averages,
            "recent_activities": recent_activities,
            "total_records": len(recent_scores),
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

    # ===== 内容管理 =====

    def get_content_list(self, content_type: str, db: Session) -> List[Dict]:
        """获取内容列表（题库/跟读/资料/配音）"""
        if content_type == "questions":
            items = db.query(AssessmentQuestion).order_by(AssessmentQuestion.id).all()
            return [{
                "id": q.id, "content": q.question_text,
                "type": q.question_type, "difficulty": q.difficulty,
                "dimension": q.dimension,
            } for q in items]

        elif content_type == "shadow":
            items = db.query(PronunciationContent).filter(PronunciationContent.is_active == 1).order_by(PronunciationContent.id).all()
            return [{
                "id": c.id, "word": c.content_text,
                "ipa": c.phonetic_ipa or "",
                "difficulty": c.cefr_level, "type": c.content_type,
            } for c in items]

        elif content_type == "materials":
            items = db.query(LearningMaterial).filter(LearningMaterial.is_active == 1).order_by(LearningMaterial.id).all()
            return [{
                "id": m.id, "title": m.title,
                "type": m.material_type, "category": m.category or "",
                "level": m.cefr_level,
            } for m in items]

        elif content_type == "dubbing":
            items = db.query(DubbingContent).filter(DubbingContent.is_active == 1).order_by(DubbingContent.id).all()
            return [{
                "id": d.id, "title": d.title,
                "line": d.dialogue_text or "", "difficulty": d.difficulty_level or "",
            } for d in items]

        return []

    # ===== 反馈管理 =====

    def get_feedbacks(self, page: int, page_size: int, status: str, db: Session) -> Dict:
        """获取反馈列表（分页+状态筛选）"""
        query = db.query(UserFeedback)
        if status:
            query = query.filter(UserFeedback.status == status)

        total = query.count()
        items = (
            query.order_by(UserFeedback.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        result = []
        for f in items:
            user = db.query(UserProfile).filter(UserProfile.id == f.user_id).first()
            result.append({
                "id": f.id,
                "user_id": f.user_id,
                "username": user.username if user else "未知",
                "content": f.content,
                "feedback_type": f.feedback_type,
                "status": f.status,
                "admin_reply": f.admin_reply,
                "replied_at": f.replied_at.isoformat() if f.replied_at else None,
                "created_at": f.created_at.isoformat() if f.created_at else "",
            })

        return {"feedbacks": result, "total": total}

    def reply_feedback(self, feedback_id: int, reply: str, admin_id: int, db: Session) -> Dict:
        """回复反馈"""
        fb = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
        if not fb:
            raise ValueError("反馈不存在")

        fb.admin_reply = reply
        fb.replied_at = datetime.utcnow()
        fb.status = "resolved"
        db.flush()

        db.add(AdminLog(
            admin_id=admin_id,
            action="feedback_reply",
            target_type="feedback",
            target_id=feedback_id,
            detail=f"回复反馈: {reply[:100]}",
        ))
        db.flush()

        user = db.query(UserProfile).filter(UserProfile.id == fb.user_id).first()
        return {
            "id": fb.id, "user_id": fb.user_id,
            "username": user.username if user else "未知",
            "content": fb.content, "feedback_type": fb.feedback_type,
            "status": fb.status, "admin_reply": fb.admin_reply,
            "replied_at": fb.replied_at.isoformat() if fb.replied_at else None,
            "created_at": fb.created_at.isoformat() if fb.created_at else "",
        }

    def resolve_feedback(self, feedback_id: int, admin_id: int, db: Session) -> Dict:
        """标记反馈为已解决"""
        fb = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
        if not fb:
            raise ValueError("反馈不存在")

        fb.status = "resolved"
        db.flush()

        db.add(AdminLog(
            admin_id=admin_id,
            action="feedback_resolve",
            target_type="feedback",
            target_id=feedback_id,
            detail="标记反馈为已解决",
        ))
        db.flush()

        user = db.query(UserProfile).filter(UserProfile.id == fb.user_id).first()
        return {
            "id": fb.id, "user_id": fb.user_id,
            "username": user.username if user else "未知",
            "content": fb.content, "feedback_type": fb.feedback_type,
            "status": fb.status, "admin_reply": fb.admin_reply,
            "replied_at": fb.replied_at.isoformat() if fb.replied_at else None,
            "created_at": fb.created_at.isoformat() if fb.created_at else "",
        }


# 单例
teacher_service = TeacherService()
admin_service = AdminService()