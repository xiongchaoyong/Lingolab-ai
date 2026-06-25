"""模块6 后台管理种子数据 — 教师/班级/作业/管理员"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission, AdminLog
from app.models.user import UserProfile

db = SessionLocal()

try:
    # 确保有教师用户
    teacher = db.query(UserProfile).filter(UserProfile.role == "teacher").first()
    if not teacher:
        teacher = UserProfile(
            username="teacher_wang",
            email="teacher_wang@lingolab.com",
            password_hash=hash_password("test123"),
            age=30,
            age_group="职场",
            learning_goal="商务",
            role="teacher",
            level_final="C1",
            is_active=1,
        )
        db.add(teacher)
        db.flush()
        print(f"创建教师用户: {teacher.username} (ID={teacher.id})")

    # 确保有管理员用户
    admin = db.query(UserProfile).filter(UserProfile.role == "admin").first()
    if not admin:
        admin = UserProfile(
            username="admin",
            email="admin@lingolab.com",
            password_hash=hash_password("admin123"),
            age=28,
            age_group="职场",
            learning_goal="商务",
            role="admin",
            level_final="C2",
            is_active=1,
        )
        db.add(admin)
        db.flush()
        print(f"创建管理员用户: {admin.username} (ID={admin.id})")

    # 创建班级
    if db.query(Class).count() == 0:
        classes_data = [
            {"name": "初级英语A班", "description": "零基础入门，打好发音和词汇基础", "level_range": "A1-A2"},
            {"name": "中级口语B班", "description": "提升日常对话流利度", "level_range": "B1-B2"},
            {"name": "高级英语C班", "description": "学术英语和商务英语进阶", "level_range": "C1-C2"},
        ]
        for cd in classes_data:
            import secrets
            cls = Class(
                name=cd["name"],
                description=cd["description"],
                teacher_id=teacher.id,
                invite_code="LINGO-" + secrets.token_hex(3).upper(),
                level_range=cd["level_range"],
                student_count=0,
            )
            db.add(cls)
        db.flush()
        print("创建3个班级")

    # 添加学生到班级
    if db.query(ClassStudent).count() == 0:
        classes = db.query(Class).all()
        students = db.query(UserProfile).filter(UserProfile.role == "learner").limit(10).all()
        for i, student in enumerate(students):
            cls = classes[i % len(classes)]
            db.add(ClassStudent(class_id=cls.id, user_id=student.id))
            cls.student_count += 1
        db.flush()
        print(f"添加{len(students)}名学生到班级")

    # 创建作业
    if db.query(Assignment).count() == 0:
        classes = db.query(Class).all()
        from datetime import datetime, timedelta
        assignments_data = [
            {"title": "Unit 3 单词跟读练习", "content_type": "pronunciation", "content_ids": [1, 2, 3]},
            {"title": "餐厅场景对话练习", "content_type": "conversation", "content_ids": [101, 102]},
            {"title": "电影片段配音挑战", "content_type": "dubbing", "content_ids": [201]},
        ]
        for i, ad in enumerate(assignments_data):
            cls = classes[i % len(classes)]
            assignment = Assignment(
                class_id=cls.id,
                title=ad["title"],
                description="请认真完成，截止日期前提交录音",
                content_type=ad["content_type"],
                content_ids=ad["content_ids"],
                due_date=datetime.utcnow() + timedelta(days=7),
            )
            db.add(assignment)
        db.flush()
        print("创建3个作业")

    # 创建提交记录
    if db.query(AssignmentSubmission).count() == 0:
        assignments = db.query(Assignment).all()
        students = db.query(UserProfile).filter(UserProfile.role == "learner").limit(5).all()
        for student in students:
            for assignment in assignments[:2]:
                db.add(AssignmentSubmission(
                    assignment_id=assignment.id,
                    user_id=student.id,
                    audio_url=f"/uploads/audio/user_{student.id}_assignment_{assignment.id}.wav",
                    score=75.0 + (student.id % 20),
                    status="submitted",
                ))
        db.flush()
        print(f"创建{len(students) * 2}条提交记录")

    # 创建管理员操作日志
    if db.query(AdminLog).count() == 0:
        db.add(AdminLog(
            admin_id=admin.id,
            action="user_enable",
            target_type="user",
            target_id=1,
            detail="初始化系统",
        ))
        db.flush()
        print("创建操作日志")

    db.commit()
    print("\n模块6种子数据导入完成！")

except Exception as e:
    db.rollback()
    print(f"错误: {e}")
    raise
finally:
    db.close()