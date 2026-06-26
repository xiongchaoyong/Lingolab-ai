"""模块4 种子数据 — 为现有用户添加学习进度/积分/徽章/预测/通知数据"""
import random
import sys
from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import UserProfile
from app.models.profile import UserSkillScore
from app.models.gamification import UserScore, UserBadge, LearningPrediction, Notice

USER_ID = 4  # xxxcy, B2 level

db = SessionLocal()

# 清理旧数据
for model in [UserSkillScore, UserScore, UserBadge, LearningPrediction, Notice]:
    db.query(model).filter(model.user_id == USER_ID).delete()
db.commit()

print("Clearing old data for user", USER_ID)

# ============================================================
# 1. user_skill_scores — 30天技能分数（雷达图/趋势/热力图）
# ============================================================
dimensions = ["listening", "speaking", "reading", "grammar"]
skills = {
    "listening": ["listening:comprehension"],
    "speaking": ["pronunciation:phoneme_accuracy", "pronunciation:fluency"],
    "reading": ["reading:vocabulary"],
    "grammar": ["grammar:accuracy"],
}
sources = ["pronunciation", "conversation", "daily_task", "assessment"]

random.seed(42)
score_records = []
today = date.today()

for days_ago in range(30, -1, -1):
    # 每天 1-4 条记录
    n = random.choices([1, 2, 3, 4], weights=[2, 3, 3, 2])[0]
    for _ in range(n):
        dim = random.choice(dimensions)
        skill = random.choice(skills[dim])
        # 基础分 55-85，随天数有提升趋势
        base = 55 + (30 - days_ago) * 0.5 + random.uniform(-8, 8)
        score = round(min(98, max(30, base)), 1)
        created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
        score_records.append(
            UserSkillScore(
                user_id=USER_ID,
                dimension=dim,
                skill_name=skill,
                score=score,
                source=random.choice(sources),
                created_at=created,
            )
        )

db.add_all(score_records)
db.flush()
print(f"Inserted {len(score_records)} skill score records")

# ============================================================
# 2. user_scores — 积分记录（最近14天）
# ============================================================
points_config = [
    ("daily_task", 10, "完成每日任务"),
    ("challenge", 20, "完成闯关挑战"),
    ("challenge", 20, "完成闯关挑战"),
    ("challenge", 30, "完成全部闯关"),
    ("dubbing", 30, "完成配音挑战"),
    ("dubbing", 20, "配音获得高分"),
    ("streak", 20, "连续学习奖励"),
    ("pronunciation_high", 15, "发音练习高分"),
    ("share", 5, "分享学习成果"),
]

point_records = []
for days_ago in range(14, -1, -1):
    n = random.randint(1, 4)
    for _ in range(n):
        action, score, desc = random.choice(points_config)
        created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 22))
        point_records.append(
            UserScore(
                user_id=USER_ID,
                action_type=action,
                score=score,
                description=desc,
                created_at=created,
            )
        )

db.add_all(point_records)
db.flush()
print(f"Inserted {len(point_records)} point records")

# ============================================================
# 3. user_badges — 徽章
# ============================================================
badges = [
    ("newcomer", "初来乍到"),
    ("streak", "坚持之星"),
    ("pronunciation_break", "发音突破"),
    ("progress", "进步达人"),
    ("dubbing", "配音达人"),
    ("perfect", "完美发音"),
    ("scholar", "学习标兵"),
]

badge_records = []
for badge_type, badge_name in badges[:5]:  # 给前5个徽章
    awarded = datetime.utcnow() - timedelta(days=random.randint(1, 20))
    badge_records.append(
        UserBadge(
            user_id=USER_ID,
            badge_type=badge_type,
            badge_name=badge_name,
            awarded_at=awarded,
        )
    )

db.add_all(badge_records)
db.flush()
print(f"Inserted {len(badge_records)} badges")

# ============================================================
# 4. learning_predictions — 预测数据
# ============================================================
pred = LearningPrediction(
    user_id=USER_ID,
    current_score=72.5,
    trend_slope=0.35,
    target_score=85,
    predicted_days=36,
    predicted_date=(today + timedelta(days=36)),
)
db.add(pred)
db.flush()
print("Inserted learning prediction")

# ============================================================
# 5. notices — 通知
# ============================================================
notices_data = [
    ("prediction", "学习预测更新", "按当前节奏，预计 36 天后达到目标分数 85 分", "info", 0),
    ("achievement", "获得新徽章", "恭喜获得「坚持之星」徽章！", "info", 0),
    ("alert", "学习提醒", "你已经连续学习 7 天，保持这个节奏！", "info", 1),
    ("alert", "发音停滞提醒", "发音得分连续 5 天未提升，建议尝试新的跟读内容", "warning", 0),
    ("prediction", "目标更新", "目标分数已更新为 85 分", "info", 1),
]

notice_records = []
for typ, title, msg, level, is_read in notices_data:
    created = datetime.utcnow() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
    notice_records.append(
        Notice(
            user_id=USER_ID,
            type=typ,
            title=title,
            message=msg,
            level=level,
            is_read=is_read,
            created_at=created,
        )
    )

db.add_all(notice_records)
db.flush()
print(f"Inserted {len(notice_records)} notices")

# ============================================================
# Commit
# ============================================================
db.commit()
db.close()
print("\nSeed data inserted successfully for user ID", USER_ID)
print(f"  - {len(score_records)} skill scores (30 days)")
print(f"  - {len(point_records)} point records")
print(f"  - {len(badge_records)} badges")
print(f"  - 1 learning prediction")
print(f"  - {len(notice_records)} notices")