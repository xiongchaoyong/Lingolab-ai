"""补充排行榜 + 教师管理模拟数据"""
import random
import uuid
from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import UserProfile
from app.models.gamification import UserScore, UserBadge
from app.models.community import VoiceChallenge, ChallengeSubmission
from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission

random.seed(2026)

db = SessionLocal()

# 所有学习者用户
LEARNER_IDS = [3, 4, 5, 6, 7, 8, 12]
TEACHER_ID = 9  # teacher_wang
USERNAMES = {3: "Alice", 4: "xxxcy", 5: "Bob", 6: "Charlie", 7: "Diana", 8: "Eve", 12: "Frank"}

print("=" * 60)
print("补充排行榜 + 教师管理模拟数据")
print("=" * 60)

# ============================================================
# 1. 排行榜积分数据 — 为所有用户生成 UserScore 记录
# ============================================================
print("\n[1/3] 排行榜积分数据...")
action_types = ["daily_task", "challenge", "dubbing", "pronunciation_high", "streak"]
descriptions = ["完成每日任务", "闯关成功", "配音高分", "发音练习", "连续学习"]

score_count = 0
for uid in LEARNER_IDS:
    # 每人最近 14 天，每天 1-3 条积分记录
    for days_ago in range(14, -1, -1):
        n = random.randint(1, 3)
        for _ in range(n):
            db.add(UserScore(
                user_id=uid,
                action_type=random.choice(action_types),
                score=random.choice([10, 15, 20, 25, 30]),
                description=random.choice(descriptions),
                created_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 22)),
            ))
            score_count += 1
db.flush()
print(f"  -> {score_count} 条积分记录（{len(LEARNER_IDS)} 个用户）")

# ============================================================
# 2. 社区排行榜 — 为多个用户生成挑战提交
# ============================================================
print("\n[2/3] 社区排行榜数据...")
voice_challenges = db.query(VoiceChallenge).filter(VoiceChallenge.is_active == True).all()
vc_count = 0
for vc in voice_challenges:
    # 每个挑战随机 3-6 个用户参与
    participants = random.sample(LEARNER_IDS, min(random.randint(3, 6), len(LEARNER_IDS)))
    for uid in participants:
        score = random.randint(55, 98)
        db.add(ChallengeSubmission(
            challenge_id=vc.id,
            user_id=uid,
            audio_url=f"/uploads/audio/vc_{uid}_{vc.id}.wav",
            pronunciation_score=score,
            fluency_score=random.randint(50, 95),
            total_score=score,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23)),
        ))
        vc_count += 1
db.flush()
print(f"  -> {vc_count} 条挑战提交（{len(voice_challenges)} 个挑战）")

# ============================================================
# 3. 教师管理数据 — 班级 + 学生 + 作业 + 提交
# ============================================================
print("\n[3/3] 教师管理数据...")

# 检查是否已有班级
existing_classes = db.query(Class).filter(Class.teacher_id == TEACHER_ID).count()
if existing_classes > 0:
    print(f"  -> 教师已有 {existing_classes} 个班级，跳过")
else:
    # 创建 3 个班级
    class_data = [
        {"name": "初级英语A班", "description": "适合零基础学员，从音标和基础词汇开始", "level_range": "A1-A2"},
        {"name": "中级英语B班", "description": "面向有一定基础的学员，提升日常会话能力", "level_range": "B1-B2"},
        {"name": "高级口语C班", "description": "针对高级学员，强化商务英语和演讲能力", "level_range": "C1-C2"},
    ]
    classes = []
    for i, cd in enumerate(class_data):
        cls = Class(
            name=cd["name"],
            description=cd["description"],
            teacher_id=TEACHER_ID,
            invite_code=f"LINGO{random.randint(1000, 9999)}",
            level_range=cd["level_range"],
            student_count=0,
            is_active=1,
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
        )
        db.add(cls)
        db.flush()
        classes.append(cls)
    print(f"  -> 创建 {len(classes)} 个班级")

    # 添加学生到班级
    student_assignments = [
        (classes[0], [3, 5, 6]),      # A班: Alice, Bob, Charlie
        (classes[1], [4, 7, 8, 12]),  # B班: xxxcy, Diana, Eve, Frank
        (classes[2], [4, 7, 12]),     # C班: xxxcy, Diana, Frank
    ]
    total_enrollments = 0
    for cls, student_ids in student_assignments:
        for sid in student_ids:
            db.add(ClassStudent(
                class_id=cls.id,
                user_id=sid,
                joined_at=datetime.utcnow() - timedelta(days=random.randint(7, 60)),
            ))
            total_enrollments += 1
        cls.student_count = len(student_ids)
    db.flush()
    print(f"  -> {total_enrollments} 名学生加入班级")

    # 创建作业
    assignment_templates = [
        {"title": "Unit 3 单词跟读练习", "content_type": "pronunciation", "content_ids": [1, 2, 3]},
        {"title": "餐厅场景对话练习", "content_type": "conversation", "content_ids": [4, 5]},
        {"title": "Toy Story 配音挑战", "content_type": "dubbing", "content_ids": [1]},
        {"title": "自我介绍练习", "content_type": "pronunciation", "content_ids": [6, 7]},
        {"title": "购物场景对话", "content_type": "conversation", "content_ids": [8]},
    ]
    assignment_count = 0
    for cls in classes:
        n = random.randint(2, 4)
        selected = random.sample(assignment_templates, n)
        for i, tmpl in enumerate(selected):
            days_ago = random.randint(3, 25)
            due_offset = random.randint(5, 14)
            assignment = Assignment(
                class_id=cls.id,
                title=f"[{cls.name}] {tmpl['title']}",
                description=f"请完成{tmpl['title']}，截止日期前提交录音",
                content_type=tmpl["content_type"],
                content_ids=tmpl["content_ids"],
                due_date=datetime.utcnow() - timedelta(days=days_ago) + timedelta(days=due_offset),
                completion_rate=round(random.uniform(30, 90), 1),
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db.add(assignment)
            db.flush()
            assignment_count += 1

            # 获取该班级学生
            class_students = (
                db.query(ClassStudent)
                .filter(ClassStudent.class_id == cls.id)
                .all()
            )
            # 为每个学生创建提交（部分学生已提交）
            for cs in class_students:
                if random.random() < 0.7:  # 70% 提交率
                    ai_score = round(random.uniform(55, 95), 1)
                    status = "reviewed" if random.random() < 0.4 else "submitted"
                    sub = AssignmentSubmission(
                        assignment_id=assignment.id,
                        user_id=cs.user_id,
                        audio_url=f"/uploads/audio/assign_{assignment.id}_{cs.user_id}.wav",
                        score=ai_score,
                        teacher_feedback=random.choice([
                            "发音清晰，继续保持！",
                            "注意语调变化，多加练习",
                            "进步很大，节奏感有提升",
                            "连读部分需要加强",
                            None,
                        ]) if status == "reviewed" else None,
                        teacher_score=round(random.uniform(60, 98), 1) if status == "reviewed" else None,
                        status=status,
                        submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, days_ago)),
                    )
                    db.add(sub)
    db.flush()
    print(f"  -> {assignment_count} 个作业")

# ============================================================
# 提交
# ============================================================
db.commit()
db.close()

print("\n" + "=" * 60)
print("补充数据完成！")
print(f"  排行榜积分: {score_count} 条")
print(f"  挑战提交: {vc_count} 条")
print("=" * 60)