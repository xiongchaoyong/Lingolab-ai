"""学生端服务 — 我的班级 + 我的作业"""

import logging
from typing import Dict, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission
from app.models.user import UserProfile

logger = logging.getLogger(__name__)


class StudentService:
    """学生端服务"""

    def get_my_classes(self, user_id: int, db: Session) -> List[Dict]:
        """获取我加入的班级列表"""
        rows = (
            db.query(ClassStudent, Class)
            .join(Class, ClassStudent.class_id == Class.id)
            .filter(ClassStudent.user_id == user_id, Class.is_active == 1)
            .order_by(ClassStudent.joined_at.desc())
            .all()
        )
        result = []
        for cs, cls in rows:
            teacher = db.query(UserProfile).filter(UserProfile.id == cls.teacher_id).first()
            result.append({
                "id": cls.id,
                "name": cls.name,
                "description": cls.description or "",
                "level_range": cls.level_range or "",
                "teacher_name": teacher.username if teacher else "未知",
                "student_count": cls.student_count,
                "joined_at": cs.joined_at.isoformat() if cs.joined_at else "",
            })
        return result

    def get_my_assignments(self, user_id: int, db: Session) -> List[Dict]:
        """获取我的作业列表（我所在班级的所有作业 + 提交状态）"""
        # 获取我加入的班级 ID
        class_ids = [
            cs.class_id for cs in
            db.query(ClassStudent).filter(ClassStudent.user_id == user_id).all()
        ]
        if not class_ids:
            return []

        assignments = (
            db.query(Assignment)
            .filter(Assignment.class_id.in_(class_ids))
            .order_by(Assignment.created_at.desc())
            .all()
        )

        result = []
        for a in assignments:
            cls = db.query(Class).filter(Class.id == a.class_id).first()
            # 查找我的提交
            submission = (
                db.query(AssignmentSubmission)
                .filter(
                    AssignmentSubmission.assignment_id == a.id,
                    AssignmentSubmission.user_id == user_id,
                )
                .first()
            )
            result.append({
                "id": a.id,
                "class_id": a.class_id,
                "class_name": cls.name if cls else "",
                "title": a.title,
                "description": a.description,
                "content_type": a.content_type,
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "created_at": a.created_at.isoformat() if a.created_at else "",
                "my_submission": {
                    "id": submission.id,
                    "score": float(submission.score) if submission and submission.score else None,
                    "teacher_feedback": submission.teacher_feedback if submission else None,
                    "teacher_score": float(submission.teacher_score) if submission and submission.teacher_score else None,
                    "status": submission.status if submission else "not_submitted",
                    "submitted_at": submission.submitted_at.isoformat() if submission and submission.submitted_at else None,
                } if submission else None,
            })
        return result

    def submit_assignment(self, user_id: int, assignment_id: int, audio_url: str, db: Session) -> Dict:
        """提交作业"""
        # 验证作业存在
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise ValueError("作业不存在")

        # 验证学生在班级中
        is_member = (
            db.query(ClassStudent)
            .filter(
                ClassStudent.class_id == assignment.class_id,
                ClassStudent.user_id == user_id,
            )
            .first()
        )
        if not is_member:
            raise ValueError("你不在该班级中，无法提交作业")

        # 检查是否已提交
        existing = (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.user_id == user_id,
            )
            .first()
        )
        if existing:
            # 更新已有提交
            existing.audio_url = audio_url
            existing.submitted_at = datetime.utcnow()
            existing.status = "submitted"
            db.flush()
            return {
                "id": existing.id, "assignment_id": assignment_id,
                "audio_url": existing.audio_url, "status": existing.status,
                "submitted_at": existing.submitted_at.isoformat(),
                "message": "作业已更新",
            }

        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            user_id=user_id,
            audio_url=audio_url,
            status="submitted",
        )
        db.add(submission)
        db.flush()

        # 更新完成率
        total_students = db.query(func.count(ClassStudent.id)).filter(
            ClassStudent.class_id == assignment.class_id
        ).scalar() or 1
        submitted_count = db.query(func.count(AssignmentSubmission.id)).filter(
            AssignmentSubmission.assignment_id == assignment_id
        ).scalar() or 0
        assignment.completion_rate = round(submitted_count / total_students * 100, 1)

        db.flush()
        return {
            "id": submission.id, "assignment_id": assignment_id,
            "audio_url": submission.audio_url, "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat(),
            "message": "提交成功",
        }


student_service = StudentService()