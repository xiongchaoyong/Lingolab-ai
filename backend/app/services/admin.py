"""后台管理服务 — 教师端班级+作业 / 运营端用户+仪表盘"""

import logging
import secrets
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission, AdminLog, UserFeedback
from app.models.user import UserProfile
from app.models.profile import UserSkillScore
from app.models.assessment import AssessmentQuestion
from app.models.pronunciation import PronunciationContent, PronunciationRecord
from app.models.learning import LearningMaterial
from app.models.gamification import DubbingContent, UserScore
from app.models.knowledge_graph import DailyTask
from app.models.conversation import ConversationSession
from app.models.knowledge_base import KnowledgeDocument, SearchLog

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
            invite_expires_at=datetime.utcnow() + timedelta(hours=24),
            level_range=level_range,
        )
        db.add(cls)
        db.flush()
        return {
            "id": cls.id, "name": cls.name, "description": cls.description or "",
            "level_range": cls.level_range or "", "student_count": 0,
            "invite_code": cls.invite_code, "is_active": cls.is_active,
            "invite_expires_at": cls.invite_expires_at.isoformat() if cls.invite_expires_at else None,
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

        # 检查邀请码是否过期
        if cls.invite_expires_at and cls.invite_expires_at < datetime.utcnow():
            raise ValueError("邀请码已过期，请联系教师刷新")

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

    def refresh_invite_code(self, class_id: int, teacher_id: int, db: Session) -> Dict:
        """刷新邀请码"""
        cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")
        cls.invite_code = "LINGO-" + secrets.token_hex(3).upper()
        cls.invite_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.flush()
        return {"invite_code": cls.invite_code, "invite_expires_at": cls.invite_expires_at.isoformat()}

    def update_class(self, class_id: int, teacher_id: int, data: Dict, db: Session) -> Dict:
        """编辑班级信息"""
        cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")

        if "name" in data and data["name"]:
            cls.name = data["name"]
        if "description" in data:
            cls.description = data["description"]
        if "level_range" in data:
            cls.level_range = data["level_range"]
        db.flush()
        return {
            "id": cls.id, "name": cls.name, "description": cls.description or "",
            "level_range": cls.level_range or "", "student_count": cls.student_count,
            "invite_code": cls.invite_code, "is_active": cls.is_active,
            "created_at": cls.created_at.isoformat() if cls.created_at else "",
        }

    def delete_class(self, class_id: int, teacher_id: int, db: Session) -> Dict:
        """删除班级（软删除）"""
        cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")
        cls.is_active = 0
        db.flush()
        return {"id": cls.id, "deleted": True}

    def remove_student(self, class_id: int, user_id: int, teacher_id: int, db: Session) -> Dict:
        """从班级移除学生"""
        cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher_id).first()
        if not cls:
            raise ValueError("班级不存在")

        membership = (
            db.query(ClassStudent)
            .filter(ClassStudent.class_id == class_id, ClassStudent.user_id == user_id)
            .first()
        )
        if not membership:
            raise ValueError("学生不在该班级中")

        db.delete(membership)
        cls.student_count = max(0, cls.student_count - 1)
        db.flush()
        return {"class_id": class_id, "user_id": user_id, "removed": True}

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
        """布置作业（支持单个班级或批量多个班级）"""
        # 解析班级 ID 列表
        class_ids = []
        if data.get("class_ids"):
            class_ids = [int(cid) for cid in data["class_ids"]]
        elif data.get("class_id"):
            class_ids = [int(data["class_id"])]

        if not class_ids:
            raise ValueError("请选择至少一个班级")

        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])

        created = []
        for cid in class_ids:
            cls = db.query(Class).filter(Class.id == cid, Class.teacher_id == teacher_id).first()
            if not cls:
                continue

            assignment = Assignment(
                class_id=cid,
                title=data["title"],
                description=data.get("description", ""),
                content_type=data["content_type"],
                content_ids=data.get("content_ids", []),
                due_date=due_date,
            )
            db.add(assignment)
            db.flush()
            created.append({
                "id": assignment.id, "class_id": assignment.class_id,
                "class_name": cls.name,
                "title": assignment.title, "description": assignment.description,
                "content_type": assignment.content_type,
                "content_ids": assignment.content_ids or [],
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "completion_rate": 0.0,
                "created_at": assignment.created_at.isoformat() if assignment.created_at else "",
            })

        return {"assignments": created, "count": len(created)}

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
                "source_type": s.source,
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


    # ===== 教师工作台 Dashboard =====

    def get_teacher_dashboard(self, teacher_id: int, db: Session) -> Dict:
        """教师工作台聚合数据"""
        # 班级列表
        classes = db.query(Class).filter(Class.teacher_id == teacher_id, Class.is_active == 1).all()
        class_ids = [c.id for c in classes]
        total_classes = len(classes)

        # 学生总数
        total_students = 0
        class_student_counts = []
        if class_ids:
            student_rows = (
                db.query(ClassStudent.class_id, func.count(ClassStudent.id))
                .filter(ClassStudent.class_id.in_(class_ids))
                .group_by(ClassStudent.class_id)
                .all()
            )
            class_map = dict(student_rows)
            for c in classes:
                count = class_map.get(c.id, 0)
                class_student_counts.append({"name": c.name, "count": count})
                total_students += count

        # 待点评作业数
        pending_reviews = 0
        if class_ids:
            pending_reviews = (
                db.query(func.count(AssignmentSubmission.id))
                .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
                .filter(Assignment.class_id.in_(class_ids), AssignmentSubmission.status == "submitted")
                .scalar()
            ) or 0

        # 总作业数
        total_assignments = 0
        if class_ids:
            total_assignments = (
                db.query(func.count(Assignment.id))
                .filter(Assignment.class_id.in_(class_ids))
                .scalar()
            ) or 0

        # 今日活跃学生数
        today = datetime.utcnow().date()
        active_students_today = 0
        if class_ids:
            student_ids = [cs.user_id for cs in db.query(ClassStudent).filter(ClassStudent.class_id.in_(class_ids)).all()]
            if student_ids:
                active_students_today = (
                    db.query(func.count(func.distinct(UserSkillScore.user_id)))
                    .filter(
                        UserSkillScore.user_id.in_(student_ids),
                        func.date(UserSkillScore.created_at) == today,
                    )
                    .scalar()
                ) or 0

        # 最近布置的作业（最新 5 条）
        recent_assignments = []
        if class_ids:
            recent = (
                db.query(Assignment)
                .filter(Assignment.class_id.in_(class_ids))
                .order_by(Assignment.created_at.desc())
                .limit(5)
                .all()
            )
            for a in recent:
                cls_name = ""
                for c in classes:
                    if c.id == a.class_id:
                        cls_name = c.name
                        break
                recent_assignments.append({
                    "id": a.id, "class_id": a.class_id,
                    "class_name": cls_name,
                    "title": a.title, "description": a.description,
                    "content_type": a.content_type,
                    "content_ids": a.content_ids or [],
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "completion_rate": float(a.completion_rate) if a.completion_rate else 0.0,
                    "created_at": a.created_at.isoformat() if a.created_at else "",
                })

        return {
            "total_classes": total_classes,
            "total_students": total_students,
            "pending_reviews": pending_reviews,
            "total_assignments": total_assignments,
            "active_students_today": active_students_today,
            "avg_class_size": round(total_students / total_classes, 1) if total_classes > 0 else 0,
            "recent_assignments": recent_assignments,
            "class_student_counts": class_student_counts,
        }

    # ===== 学生进度趋势 =====

    def get_student_trend(self, student_id: int, teacher_id: int, db: Session) -> Dict:
        """获取学生四维分数趋势（近30天，按天分组）"""
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

        start = datetime.utcnow() - timedelta(days=30)
        rows = (
            db.query(
                func.date(UserSkillScore.created_at).label("date"),
                UserSkillScore.dimension,
                func.avg(UserSkillScore.score),
            )
            .filter(
                UserSkillScore.user_id == student_id,
                UserSkillScore.created_at >= start,
                UserSkillScore.dimension.in_(["pronunciation", "fluency", "grammar", "vocabulary"]),
            )
            .group_by(func.date(UserSkillScore.created_at), UserSkillScore.dimension)
            .order_by("date")
            .all()
        )

        # pivot by date
        by_date = {}
        for row in rows:
            d = str(row[0])
            if d not in by_date:
                by_date[d] = {"pronunciation": 0, "fluency": 0, "grammar": 0, "vocabulary": 0}
            by_date[d][str(row[1])] = round(float(row[2]), 1)

        trend = [
            {"date": d, **scores} for d, scores in sorted(by_date.items())
        ]
        return {"trend": trend}

    # ===== 学习打卡统计 =====

    def get_student_checkin_stats(self, student_id: int, teacher_id: int, db: Session) -> Dict:
        """获取学生近30天每日打卡统计"""
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

        start = datetime.utcnow() - timedelta(days=30)
        rows = (
            db.query(
                func.date(UserSkillScore.created_at).label("date"),
                func.count(UserSkillScore.id),
            )
            .filter(
                UserSkillScore.user_id == student_id,
                UserSkillScore.created_at >= start,
            )
            .group_by(func.date(UserSkillScore.created_at))
            .order_by("date")
            .all()
        )

        existing = {str(r[0]): r[1] for r in rows}

        checkins = []
        streak = 0
        today = datetime.utcnow().date()
        for i in range(30, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            count = existing.get(d, 0)
            checkins.append({"date": d, "completed": count, "total": count})

        # 计算连续打卡天数（从今天往前算）
        for i in range(31):
            d = (today - timedelta(days=i)).isoformat()
            if existing.get(d, 0) > 0:
                streak += 1
            else:
                break

        total_days = sum(1 for c in checkins if c["completed"] > 0)
        return {
            "checkins": checkins,
            "streak": streak,
            "total_days": total_days,
            "completion_rate": round(total_days / 31 * 100, 1) if total_days > 0 else 0,
        }


class AdminService:
    """运营端服务"""

    @staticmethod
    def _rag():
        """懒加载 RAG 服务 — 避免模块导入时触发 torch 加载"""
        from app.services.rag_service import rag_service
        return rag_service

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
        if user_id == admin_id:
            raise ValueError("不能禁用自己的账号")

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

    def set_user_role(self, user_id: int, role: str, admin_id: int, db: Session) -> Dict:
        """修改用户角色"""
        if user_id == admin_id:
            raise ValueError("不能修改自己的角色")

        valid_roles = ("learner", "teacher", "admin")
        if role not in valid_roles:
            raise ValueError(f"无效角色: {role}，可选值: {', '.join(valid_roles)}")

        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        old_role = user.role
        user.role = role
        db.flush()

        db.add(AdminLog(
            admin_id=admin_id,
            action="user_role_change",
            target_type="user",
            target_id=user_id,
            detail=f"用户角色 {old_role} → {role}",
        ))
        db.flush()
        return {"id": user.id, "role": user.role}

    def get_user_detail(self, user_id: int, db: Session) -> Dict:
        """获取用户详细信息（含学习统计）"""
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 维度分数
        dim_scores = {}
        scores = (
            db.query(UserSkillScore)
            .filter(UserSkillScore.user_id == user_id)
            .order_by(UserSkillScore.created_at.desc())
            .limit(50)
            .all()
        )
        for s in scores:
            dim = s.dimension
            if dim not in dim_scores:
                dim_scores[dim] = []
            dim_scores[dim].append(float(s.score))

        dimension_averages = {
            dim: round(sum(vals) / len(vals), 1)
            for dim, vals in dim_scores.items()
        } if dim_scores else {}

        # 积分
        total_points_raw = (
            db.query(func.sum(UserScore.score)).filter(UserScore.user_id == user_id).scalar()
        )
        total_points = float(total_points_raw) if total_points_raw else 0

        # 对话次数
        conversation_count = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user_id)
            .scalar()
        ) or 0

        # 发音练习次数
        pronunciation_count = (
            db.query(func.count(PronunciationRecord.id))
            .filter(PronunciationRecord.user_id == user_id)
            .scalar()
        ) or 0

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "age_group": user.age_group,
            "learning_goal": user.learning_goal,
            "level_self": user.level_self,
            "level_test": user.level_test,
            "level_final": user.level_final,
            "is_active": user.is_active,
            "assessment_completed": user.assessment_completed,
            "total_points": total_points,
            "conversation_count": conversation_count,
            "pronunciation_count": pronunciation_count,
            "dimension_averages": dimension_averages,
            "created_at": user.created_at.isoformat() if user.created_at else "",
        }

    def get_dashboard(self, db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """获取运营仪表盘数据"""
        today = date.today()

        # 解析日期范围（默认最近30天）
        if start_date:
            range_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            range_start = today - timedelta(days=30)
        if end_date:
            range_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            range_end = today

        # 总用户数
        total_users = db.query(func.count(UserProfile.id)).scalar() or 0
        active_users = db.query(func.count(UserProfile.id)).filter(UserProfile.is_active == 1).scalar() or 0

        # 角色分布
        teacher_count = db.query(func.count(UserProfile.id)).filter(UserProfile.role == 'teacher').scalar() or 0
        learner_count = db.query(func.count(UserProfile.id)).filter(UserProfile.role == 'learner').scalar() or 0

        # 班级概况
        total_classes = db.query(func.count(Class.id)).filter(Class.is_active == 1).scalar() or 0
        total_class_students = db.query(func.count(ClassStudent.user_id)).scalar() or 0
        avg_students_per_class = round(total_class_students / total_classes, 1) if total_classes > 0 else 0

        # 真实对话完成率
        conversation_total = db.query(func.count(ConversationSession.id)).scalar() or 0
        conversation_completed = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.status == 'completed')
            .scalar()
        ) or 0
        conversation_completion = round(conversation_completed / conversation_total * 100, 1) if conversation_total > 0 else 0.0

        # 任务完成率
        task_total = db.query(func.count(DailyTask.id)).scalar() or 0
        task_completed = (
            db.query(func.count(DailyTask.id))
            .filter(DailyTask.status == 'completed')
            .scalar()
        ) or 0
        task_completion_rate = round(task_completed / task_total * 100, 1) if task_total > 0 else 0.0

        # 今日活动
        today_tasks_completed = (
            db.query(func.count(DailyTask.id))
            .filter(DailyTask.task_date == today, DailyTask.status == 'completed')
            .scalar()
        ) or 0
        today_pronunciation = (
            db.query(func.count(PronunciationRecord.id))
            .filter(func.date(PronunciationRecord.created_at) == today)
            .scalar()
        ) or 0
        today_conversations = (
            db.query(func.count(ConversationSession.id))
            .filter(func.date(ConversationSession.created_at) == today)
            .scalar()
        ) or 0

        # 总积分
        total_points = db.query(func.sum(UserScore.score)).scalar() or 0

        # DAU — 今日活跃用户（多表 union）
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

        # 日新增
        daily_new_users = (
            db.query(func.count(UserProfile.id))
            .filter(func.date(UserProfile.created_at) == today)
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

        # 7 日 DAU 趋势
        daily_activity = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = (
                db.query(func.count(func.distinct(UserSkillScore.user_id)))
                .filter(func.date(UserSkillScore.created_at) == d)
                .scalar()
            ) or 0
            daily_activity.append({"label": d.strftime("%m/%d"), "value": count})

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

        # 留存率计算
        retention_d1 = 0.0
        retention_d7 = 0.0

        yesterday = today - timedelta(days=1)
        yesterday_active = (
            db.query(func.count(func.distinct(UserSkillScore.user_id)))
            .filter(func.date(UserSkillScore.created_at) == yesterday)
            .scalar()
        ) or 0

        if yesterday_active > 0:
            yesterday_users = (
                db.query(UserSkillScore.user_id.label('uid'))
                .filter(func.date(UserSkillScore.created_at) == yesterday)
                .distinct()
                .subquery()
            )
            today_from_yesterday = (
                db.query(func.count(func.distinct(UserSkillScore.user_id)))
                .filter(
                    func.date(UserSkillScore.created_at) == today,
                    UserSkillScore.user_id.in_(
                        db.query(yesterday_users.c.uid).select_from(yesterday_users)
                    )
                )
                .scalar()
            ) or 0
            retention_d1 = round(today_from_yesterday / yesterday_active * 100, 1)

        seven_days_ago = today - timedelta(days=7)
        seven_ago_active = (
            db.query(func.count(func.distinct(UserSkillScore.user_id)))
            .filter(func.date(UserSkillScore.created_at) == seven_days_ago)
            .scalar()
        ) or 0

        if seven_ago_active > 0:
            seven_ago_users = (
                db.query(UserSkillScore.user_id.label('uid'))
                .filter(func.date(UserSkillScore.created_at) == seven_days_ago)
                .distinct()
                .subquery()
            )
            today_from_seven = (
                db.query(func.count(func.distinct(UserSkillScore.user_id)))
                .filter(
                    func.date(UserSkillScore.created_at) == today,
                    UserSkillScore.user_id.in_(
                        db.query(seven_ago_users.c.uid).select_from(seven_ago_users)
                    )
                )
                .scalar()
            ) or 0
            retention_d7 = round(today_from_seven / seven_ago_active * 100, 1)

        # 总学习时长（分钟）
        total_duration = (
            db.query(func.count(UserSkillScore.id)).scalar()
        ) or 0
        total_duration_minutes = total_duration * 5  # 每条记录约5分钟

        # 人均时长
        active_user_count = db.query(func.count(func.distinct(UserSkillScore.user_id))).scalar() or 1
        avg_duration_minutes = round(total_duration_minutes / active_user_count, 1)

        # ===== 内容使用排行 =====
        content_ranking = []

        # 热门发音内容 Top 8
        pron_rows = (
            db.query(PronunciationContent.content_text, func.count(PronunciationRecord.id))
            .join(PronunciationRecord, PronunciationRecord.content_id == PronunciationContent.id)
            .filter(
                func.date(PronunciationRecord.created_at) >= range_start,
                func.date(PronunciationRecord.created_at) <= range_end,
            )
            .group_by(PronunciationContent.content_text)
            .order_by(func.count(PronunciationRecord.id).desc())
            .limit(8)
            .all()
        )
        for text, count in pron_rows:
            content_ranking.append({"name": text, "type": "发音练习", "count": count})

        # 热门对话场景 Top 6
        scene_rows = (
            db.query(ConversationSession.scene, func.count(ConversationSession.id))
            .filter(
                func.date(ConversationSession.created_at) >= range_start,
                func.date(ConversationSession.created_at) <= range_end,
            )
            .group_by(ConversationSession.scene)
            .order_by(func.count(ConversationSession.id).desc())
            .limit(6)
            .all()
        )
        scene_labels = {
            "self_intro": "自我介绍", "directions": "问路指路", "shopping": "购物",
            "restaurant": "餐厅点餐", "free": "自由对话", "hotel": "酒店入住",
            "airport": "机场出行", "hospital": "医院就诊", "school": "校园生活",
        }
        for scene, count in scene_rows:
            content_ranking.append({"name": scene_labels.get(scene, scene), "type": "场景对话", "count": count})

        # 按 count 降序排列
        content_ranking.sort(key=lambda x: x["count"], reverse=True)

        # ===== 转化漏斗 =====
        registered_in_range = (
            db.query(func.count(UserProfile.id))
            .filter(func.date(UserProfile.created_at) >= range_start,
                     func.date(UserProfile.created_at) <= range_end)
            .scalar()
        ) or 0
        assessed_in_range = (
            db.query(func.count(UserProfile.id))
            .filter(UserProfile.assessment_completed == 1,
                     func.date(UserProfile.created_at) >= range_start,
                     func.date(UserProfile.created_at) <= range_end)
            .scalar()
        ) or 0

        # 有首次练习行为（发音/对话任一）
        first_practice_sub = (
            db.query(UserSkillScore.user_id.label('uid'))
            .filter(func.date(UserSkillScore.created_at) >= range_start,
                     func.date(UserSkillScore.created_at) <= range_end)
            .distinct()
            .subquery()
        )
        first_practice_count = (
            db.query(func.count(first_practice_sub.c.uid)).scalar()
        ) or 0

        # 7日留存：窗口期用户中，有活动超出 range_end 的
        retained_7d_count = 0
        if first_practice_count > 0:
            window_users = (
                db.query(UserSkillScore.user_id.label('uid'))
                .filter(func.date(UserSkillScore.created_at) >= range_start,
                         func.date(UserSkillScore.created_at) <= range_end)
                .distinct()
                .subquery()
            )
            retained_7d_count = (
                db.query(func.count(func.distinct(UserSkillScore.user_id)))
                .filter(
                    UserSkillScore.user_id.in_(
                        db.query(window_users.c.uid).select_from(window_users)
                    ),
                    func.date(UserSkillScore.created_at) > range_end,
                )
                .scalar()
            ) or 0

        conversion_funnel = {
            "registered": registered_in_range,
            "assessed": assessed_in_range,
            "first_practice": first_practice_count,
            "retained_7d": retained_7d_count,
        }

        # ===== 每日活跃日报 =====
        daily_report = []
        total_days = (range_end - range_start).days
        # 限制最多返回 60 天数据（防止超大范围）
        if total_days > 60:
            range_start = range_end - timedelta(days=59)
            total_days = 59

        current = range_start
        while current <= range_end:
            day_dau = (
                db.query(func.count(func.distinct(UserSkillScore.user_id)))
                .filter(func.date(UserSkillScore.created_at) == current)
                .scalar()
            ) or 0
            day_new = (
                db.query(func.count(UserProfile.id))
                .filter(func.date(UserProfile.created_at) == current)
                .scalar()
            ) or 0
            day_practice = (
                db.query(func.count(PronunciationRecord.id))
                .filter(func.date(PronunciationRecord.created_at) == current)
                .scalar()
            ) or 0
            day_conv = (
                db.query(func.count(ConversationSession.id))
                .filter(func.date(ConversationSession.created_at) == current)
                .scalar()
            ) or 0
            day_tasks = (
                db.query(func.count(DailyTask.id))
                .filter(DailyTask.task_date == current, DailyTask.status == "completed")
                .scalar()
            ) or 0
            daily_report.append({
                "date": current.isoformat(),
                "dau": day_dau,
                "new_users": day_new,
                "practice_count": day_practice,
                "conversation_count": day_conv,
                "tasks_completed": day_tasks,
            })
            current += timedelta(days=1)

        return {
            "metrics": {
                "dau": dau,
                "mau": mau,
                "retention_d1": retention_d1,
                "retention_d7": retention_d7,
                "total_users": total_users,
                "active_users": active_users,
                "daily_new_users": daily_new_users,
                "total_duration_minutes": total_duration_minutes,
                "avg_duration_minutes": avg_duration_minutes,
                "conversation_completion_rate": conversation_completion,
                # 新增指标
                "teacher_count": teacher_count,
                "learner_count": learner_count,
                "total_classes": total_classes,
                "avg_students_per_class": avg_students_per_class,
                "today_tasks_completed": today_tasks_completed,
                "today_pronunciation": today_pronunciation,
                "today_conversations": today_conversations,
                "task_completion_rate": task_completion_rate,
                "total_points": total_points,
            },
            "user_trend": user_trend,
            "daily_activity": daily_activity,
            "content_type_distribution": type_dist,
            "level_distribution": level_dist,
            "content_ranking": content_ranking,
            "conversion_funnel": conversion_funnel,
            "daily_report": daily_report,
        }

    # ===== 内容管理 =====

    def get_content_list(self, content_type: str, db: Session, page: int = 1, page_size: int = 20) -> Dict:
        """获取内容列表（题库/跟读/资料/配音），分页"""
        offset = (page - 1) * page_size

        if content_type == "questions":
            query = db.query(AssessmentQuestion).order_by(AssessmentQuestion.id)
            total = query.count()
            items = query.offset(offset).limit(page_size).all()
            rows = [{
                "id": q.id, "content": q.question_text,
                "type": q.dimension, "difficulty": q.difficulty,
                "dimension": q.dimension,
            } for q in items]

        elif content_type == "shadow":
            query = db.query(PronunciationContent).filter(PronunciationContent.is_active == 1).order_by(PronunciationContent.id)
            total = query.count()
            items = query.offset(offset).limit(page_size).all()
            rows = [{
                "id": c.id, "word": c.content_text,
                "ipa": c.phonetic_ipa or "",
                "difficulty": c.cefr_level, "type": c.content_type,
            } for c in items]

        elif content_type == "materials":
            query = db.query(LearningMaterial).filter(LearningMaterial.is_active == 1).order_by(LearningMaterial.id)
            total = query.count()
            items = query.offset(offset).limit(page_size).all()
            rows = [{
                "id": m.id, "title": m.title,
                "type": m.material_type, "category": m.category or "",
                "level": m.cefr_level,
            } for m in items]

        elif content_type == "dubbing":
            query = db.query(DubbingContent).filter(DubbingContent.is_active == 1).order_by(DubbingContent.id)
            total = query.count()
            items = query.offset(offset).limit(page_size).all()
            rows = [{
                "id": d.id, "title": d.title,
                "line": d.subtitle or "", "difficulty": d.difficulty or "",
            } for d in items]

        else:
            return {"items": [], "total": 0}

        return {"items": rows, "total": total}

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

    def submit_feedback(self, user_id: int, content: str, feedback_type: str, db: Session) -> Dict:
        """用户提交反馈"""
        fb = UserFeedback(
            user_id=user_id,
            content=content,
            feedback_type=feedback_type,
            status="pending",
        )
        db.add(fb)
        db.flush()
        return {
            "id": fb.id, "user_id": fb.user_id,
            "content": fb.content, "feedback_type": fb.feedback_type,
            "status": fb.status, "created_at": fb.created_at.isoformat() if fb.created_at else "",
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


# ===== 内容管理 CRUD =====

    def create_content(self, content_type: str, data: dict, admin_id: int, db: Session) -> Dict:
        """创建内容项"""
        if content_type == "questions":
            item = AssessmentQuestion(
                question_text=data["content"],
                options=data.get("options", []),
                correct_option=data.get("correct_option", 1),
                dimension=data.get("dimension", "speaking"),
                difficulty=data.get("difficulty", "A1"),
            )
        elif content_type == "shadow":
            item = PronunciationContent(
                title=data.get("title", data.get("word", "")),
                content_text=data["word"],
                content_type=data.get("type", "word"),
                cefr_level=data.get("difficulty", "A1"),
                phonetic_ipa=data.get("ipa", ""),
            )
        elif content_type == "materials":
            item = LearningMaterial(
                title=data["title"],
                description=data.get("description", ""),
                material_type=data.get("type", "article"),
                url=data.get("url", ""),
                cefr_level=data.get("level", "A1"),
                category=data.get("category", ""),
            )
        elif content_type == "dubbing":
            item = DubbingContent(
                title=data["title"],
                source=data.get("source", ""),
                difficulty=data.get("difficulty", "easy"),
                duration=data.get("duration", 10),
                subtitle=data.get("line", ""),
                audio_url=data.get("audio_url", ""),
            )
        else:
            raise ValueError("无效的内容类型")

        db.add(item)
        db.flush()

        db.add(AdminLog(
            admin_id=admin_id, action="content_create",
            target_type=content_type, target_id=item.id,
            detail=f"创建内容: {data.get('title', data.get('word', data.get('content', '')))}",
        ))
        db.flush()
        return {"id": item.id, "message": "创建成功"}

    def update_content(self, content_type: str, item_id: int, data: dict, admin_id: int, db: Session) -> Dict:
        """更新内容项"""
        model_map = {
            "questions": AssessmentQuestion,
            "shadow": PronunciationContent,
            "materials": LearningMaterial,
            "dubbing": DubbingContent,
        }
        model = model_map.get(content_type)
        if not model:
            raise ValueError("无效的内容类型")

        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise ValueError("内容不存在")

        # 字段映射
        field_map = {
            "questions": {"content": "question_text", "type": "dimension", "difficulty": "difficulty", "dimension": "dimension"},
            "shadow": {"word": "content_text", "type": "content_type", "difficulty": "cefr_level", "ipa": "phonetic_ipa"},
            "materials": {"title": "title", "type": "material_type", "level": "cefr_level", "category": "category", "description": "description"},
            "dubbing": {"title": "title", "line": "subtitle", "difficulty": "difficulty", "source": "source"},
        }

        mapping = field_map.get(content_type, {})
        for key, value in data.items():
            db_field = mapping.get(key, key)
            if hasattr(item, db_field):
                setattr(item, db_field, value)

        db.flush()

        db.add(AdminLog(
            admin_id=admin_id, action="content_update",
            target_type=content_type, target_id=item_id,
            detail=f"更新内容 ID={item_id}",
        ))
        db.flush()
        return {"id": item_id, "message": "更新成功"}

    def delete_content(self, content_type: str, item_id: int, admin_id: int, db: Session) -> Dict:
        """删除内容项（软删除）"""
        model_map = {
            "questions": AssessmentQuestion,
            "shadow": PronunciationContent,
            "materials": LearningMaterial,
            "dubbing": DubbingContent,
        }
        model = model_map.get(content_type)
        if not model:
            raise ValueError("无效的内容类型")

        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise ValueError("内容不存在")

        # 软删除：设置 is_active = 0
        if hasattr(item, "is_active"):
            item.is_active = 0
        else:
            db.delete(item)

        db.flush()

        db.add(AdminLog(
            admin_id=admin_id, action="content_delete",
            target_type=content_type, target_id=item_id,
            detail=f"删除内容 ID={item_id}",
        ))
        db.flush()
        return {"id": item_id, "message": "删除成功"}


    # ===== 知识库管理 =====

    def get_knowledge_docs(self, page: int, page_size: int, search: str, category: str, db: Session) -> Dict:
        """获取知识库文档列表（分页+搜索+分类筛选）

        优化：① 只查询需要的列 ② 在 DB 层截断 content（避免传输完整 TEXT）
        """
        # 只 select 需要的列，content 在 DB 层截断
        cols = [
            KnowledgeDocument.id,
            KnowledgeDocument.title,
            func.left(KnowledgeDocument.content, 500).label('content'),
            KnowledgeDocument.category,
            KnowledgeDocument.source_type,
            KnowledgeDocument.is_active,
            KnowledgeDocument.created_at,
            KnowledgeDocument.updated_at,
        ]
        query = db.query(*cols)

        if search:
            query = query.filter(
                KnowledgeDocument.title.contains(search) |
                KnowledgeDocument.content.contains(search)
            )
        if category:
            query = query.filter(KnowledgeDocument.category == category)

        # COUNT 查询用简化子查询（不携带 LEFT/列选择开销）
        count_query = db.query(func.count(KnowledgeDocument.id))
        if search:
            count_query = count_query.filter(
                KnowledgeDocument.title.contains(search) |
                KnowledgeDocument.content.contains(search)
            )
        if category:
            count_query = count_query.filter(KnowledgeDocument.category == category)
        total = count_query.scalar() or 0

        docs = (
            query.order_by(KnowledgeDocument.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for d in docs:
            items.append({
                "id": d.id,
                "title": d.title,
                "content": d.content or "",
                "category": d.category or "general",
                "source_type": d.source_type or "manual",
                "is_active": d.is_active if d.is_active is not None else 1,
                "created_at": d.created_at.isoformat() if d.created_at else "",
                "updated_at": d.updated_at.isoformat() if d.updated_at else "",
            })

        return {"items": items, "total": total}

    def create_knowledge_doc(self, data: Dict, admin_id: int, db: Session) -> Dict:
        """新增知识库文档并自动向量化"""
        doc = KnowledgeDocument(
            title=data["title"],
            content=data["content"],
            category=data.get("category", "general"),
            source_type="manual",
            is_active=1,
        )
        db.add(doc)
        db.flush()

        # 向量化入库
        text = f"问题：{doc.title}\n回答：{doc.content}" if doc.category == "faq" else f"{doc.title}\n{doc.content}"
        self._rag().add_document(
            str(doc.id),
            text,
            {"title": doc.title, "category": doc.category, "source_type": doc.source_type},
        )

        db.add(AdminLog(
            admin_id=admin_id, action="knowledge_create",
            target_type="knowledge", target_id=doc.id,
            detail=f"创建知识库文档: {doc.title}",
        ))
        db.flush()
        return {"id": doc.id, "title": doc.title, "message": "创建成功"}

    def update_knowledge_doc(self, doc_id: int, data: Dict, admin_id: int, db: Session) -> Dict:
        """更新知识库文档并更新向量"""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise ValueError("文档不存在")

        if "title" in data and data["title"] is not None:
            doc.title = data["title"]
        if "content" in data and data["content"] is not None:
            doc.content = data["content"]
        if "category" in data and data["category"] is not None:
            doc.category = data["category"]
        if "is_active" in data and data["is_active"] is not None:
            doc.is_active = data["is_active"]

        db.flush()

        # 更新向量
        if doc.is_active:
            text = f"问题：{doc.title}\n回答：{doc.content}" if doc.category == "faq" else f"{doc.title}\n{doc.content}"
            self._rag().add_document(
                str(doc.id),
                text,
                {"title": doc.title, "category": doc.category, "source_type": doc.source_type},
            )
        else:
            self._rag().delete_document(str(doc.id))

        db.add(AdminLog(
            admin_id=admin_id, action="knowledge_update",
            target_type="knowledge", target_id=doc_id,
            detail=f"更新知识库文档: {doc.title}",
        ))
        db.flush()
        return {"id": doc_id, "title": doc.title, "message": "更新成功"}

    def delete_knowledge_doc(self, doc_id: int, admin_id: int, db: Session) -> Dict:
        """删除知识库文档（软删除 + 从向量库移除）"""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise ValueError("文档不存在")

        doc.is_active = 0
        db.flush()

        self._rag().delete_document(str(doc_id))

        db.add(AdminLog(
            admin_id=admin_id, action="knowledge_delete",
            target_type="knowledge", target_id=doc_id,
            detail=f"删除知识库文档: {doc.title}",
        ))
        db.flush()
        return {"id": doc_id, "message": "删除成功"}

    def reindex_document(self, doc_id: int, db: Session) -> Dict:
        """重新索引单条文档"""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise ValueError("文档不存在")

        text = f"问题：{doc.title}\n回答：{doc.content}" if doc.category == "faq" else f"{doc.title}\n{doc.content}"
        ok = self._rag().add_document(
            str(doc.id),
            text,
            {"title": doc.title, "category": doc.category, "source_type": doc.source_type},
        )
        return {"id": doc_id, "success": ok, "message": "重新索引成功" if ok else "索引失败"}

    def rebuild_index(self, db: Session) -> Dict:
        """全量重建向量索引"""
        self._rag().clear()

        docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == 1).all()
        items = []
        for doc in docs:
            text = f"问题：{doc.title}\n回答：{doc.content}" if doc.category == "faq" else f"{doc.title}\n{doc.content}"
            items.append({
                "id": str(doc.id),
                "text": text,
                "metadata": {"title": doc.title, "category": doc.category, "source_type": doc.source_type},
            })

        count = self._rag().add_documents_batch(items)
        return {"total": len(docs), "indexed": count, "message": f"全量重建完成: {count}/{len(docs)} 条"}

    def get_search_logs(self, page: int, page_size: int, user_id: Optional[int], db: Session) -> Dict:
        """获取检索日志列表（分页）"""
        query = db.query(SearchLog)

        if user_id:
            query = query.filter(SearchLog.user_id == user_id)

        total = query.count()
        logs = (
            query.order_by(SearchLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for log in logs:
            username = ""
            if log.user_id:
                user = db.query(UserProfile).filter(UserProfile.id == log.user_id).first()
                username = user.username if user else ""
            items.append({
                "id": log.id,
                "user_id": log.user_id,
                "username": username,
                "query": log.query,
                "retrieved_docs": log.retrieved_docs,
                "reply": log.reply,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            })

        return {"items": items, "total": total}


# 单例
teacher_service = TeacherService()
admin_service = AdminService()