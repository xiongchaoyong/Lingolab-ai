"""全模块模拟数据种子 — 为 xxxcy 用户填充所有模块的丰富数据"""
import random
import uuid
from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import UserProfile
from app.models.profile import UserSkillScore
from app.models.pronunciation import PronunciationContent, PronunciationRecord
from app.models.conversation import ConversationSession, ConversationMessage
from app.models.gamification import (
    UserScore, UserBadge, LearningPrediction, Notice,
    DubbingContent, DubbingRecord,
)
from app.models.knowledge_graph import DailyTask, MaterialRecommendation
from app.models.learning import LearningMaterial, MaterialRecord
from app.models.community import (
    VoiceChallenge, ChallengeSubmission,
    DiscussionPost, PostComment, PostLike, StudyGroup, GroupMember,
)

USER_ID = 4  # xxxcy
random.seed(42)

db = SessionLocal()

print("=" * 60)
print("开始为 xxxcy (ID=4) 生成模拟数据...")
print("=" * 60)

# ============================================================
# 1. 发音练习记录 (pronunciation_records)
# ============================================================
print("\n[1/10] 发音练习记录...")
content_items = db.query(PronunciationContent).filter(PronunciationContent.is_active == 1).all()
pron_records = []
for days_ago in range(14, -1, -1):
    n = random.randint(1, 3)
    for _ in range(n):
        content = random.choice(content_items)
        score = round(60 + random.uniform(0, 35), 1)
        created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 22))
        pron_records.append(PronunciationRecord(
            user_id=USER_ID,
            content_id=content.id,
            mode=content.content_type,
            audio_url=f"/uploads/audio/pron_{USER_ID}_{content.id}_{days_ago}.wav",
            overall_score=score,
            phoneme_score=round(score * random.uniform(0.85, 1.05), 1),
            stress_score=round(score * random.uniform(0.80, 1.1), 1),
            intonation_score=round(score * random.uniform(0.75, 1.1), 1),
            rhythm_score=round(score * random.uniform(0.82, 1.08), 1),
            linking_score=round(score * random.uniform(0.78, 1.05), 1) if content.content_type == "sentence" else None,
            created_at=created,
        ))
db.add_all(pron_records)
db.flush()
print(f"  -> {len(pron_records)} 条发音练习记录")

# ============================================================
# 2. 对话练习记录 (conversation_sessions + messages)
# ============================================================
print("\n[2/10] 对话练习记录...")
scenes = ["restaurant", "shopping", "self_intro", "directions", "free"]
session_count = 0
msg_count = 0
for days_ago in range(10, -1, -1):
    if random.random() < 0.3:
        continue
    scene = random.choice(scenes)
    rounds = random.randint(3, 8)
    session = ConversationSession(
        user_id=USER_ID,
        session_uuid=str(uuid.uuid4()),
        scene=scene,
        cefr_level=random.choice(["A2", "B1", "B2"]),
        round_count=rounds,
        status="completed",
        score_overall=round(60 + random.uniform(0, 35), 1),
        score_pronunciation=round(60 + random.uniform(0, 30), 1),
        score_grammar=round(60 + random.uniform(0, 30), 1),
        score_vocabulary=round(60 + random.uniform(0, 30), 1),
        score_engagement=round(60 + random.uniform(0, 30), 1),
        started_at=datetime.utcnow() - timedelta(days=days_ago),
        ended_at=datetime.utcnow() - timedelta(days=days_ago, minutes=rounds * 2),
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(session)
    db.flush()
    session_count += 1

    user_messages = [
        "Hello, how can I help you today?",
        "I'd like to order something please.",
        "Can I have the menu?",
        "What do you recommend?",
        "That sounds great, I'll take that.",
        "Just water please, thank you.",
        "How long will it take?",
        "Perfect, thank you very much.",
    ]
    assistant_messages = [
        "Sure, what would you like?",
        "The special today is grilled salmon.",
        "Would you like anything to drink?",
        "About 15 minutes.",
        "You're welcome! Enjoy your meal.",
        "Is there anything else I can help with?",
        "Great choice! I'll put that order in.",
        "Have a wonderful day!",
    ]
    for turn in range(rounds):
        role = "user" if turn % 2 == 0 else "assistant"
        pool = user_messages if role == "user" else assistant_messages
        db.add(ConversationMessage(
            session_id=session.id,
            round_number=turn + 1,
            role=role,
            content_text=random.choice(pool),
            created_at=session.started_at + timedelta(seconds=turn * 30),
        ))
        msg_count += 1
db.flush()
print(f"  -> {session_count} 个对话会话, {msg_count} 条消息")

# ============================================================
# 3. 配音记录 (dubbing_records)
# ============================================================
print("\n[3/10] 配音记录...")
dubbing_items = db.query(DubbingContent).filter(DubbingContent.is_active == True).all()
dubbing_records = []
for days_ago in range(10, -1, -1):
    if random.random() < 0.5:
        continue
    item = random.choice(dubbing_items)
    score = round(55 + random.uniform(0, 40), 1)
    dubbing_records.append(DubbingRecord(
        user_id=USER_ID,
        content_id=item.id,
        audio_url=f"/uploads/audio/dub_{USER_ID}_{item.id}_{days_ago}.wav",
        total_score=score,
        pronunciation_score=round(score * random.uniform(0.85, 1.1), 1),
        intonation_score=round(score * random.uniform(0.80, 1.1), 1),
        emotion_score=round(score * random.uniform(0.75, 1.1), 1),
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
db.add_all(dubbing_records)
db.flush()
print(f"  -> {len(dubbing_records)} 条配音记录")

# ============================================================
# 4. 语音挑战参与 (community voice_challenge submissions)
# ============================================================
print("\n[4/10] 语音挑战参与...")
voice_challenges = db.query(VoiceChallenge).filter(VoiceChallenge.is_active == True).all()
vc_submissions = []
for vc in voice_challenges:
    if random.random() < 0.5:
        continue
    score = random.randint(60, 95)
    vc_submissions.append(ChallengeSubmission(
        challenge_id=vc.id,
        user_id=USER_ID,
        audio_url=f"/uploads/audio/vc_{USER_ID}_{vc.id}.wav",
        pronunciation_score=score,
        fluency_score=random.randint(55, 92),
        total_score=score,
        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
    ))
db.add_all(vc_submissions)
db.flush()
print(f"  -> {len(vc_submissions)} 条语音挑战提交")

# ============================================================
# 5. 学习资料记录 (material_records)
# ============================================================
print("\n[5/10] 学习资料阅读记录...")
materials = db.query(LearningMaterial).filter(LearningMaterial.is_active == 1).all()
mat_records = []
for days_ago in range(14, -1, -1):
    if random.random() < 0.6:
        continue
    mat = random.choice(materials)
    duration = random.randint(180, 1500)  # 秒
    action = random.choice(["viewed", "completed", "completed"])
    mat_records.append(MaterialRecord(
        user_id=USER_ID,
        material_id=mat.id,
        action=action,
        duration_seconds=duration,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
db.add_all(mat_records)
db.flush()
print(f"  -> {len(mat_records)} 条学习资料记录")

# ============================================================
# 6. 社区互动 (post_likes + comments)
# ============================================================
print("\n[6/10] 社区互动...")
posts = db.query(DiscussionPost).all()
like_count = 0
for post in posts:
    if random.random() < 0.6:
        db.add(PostLike(post_id=post.id, user_id=USER_ID))
        like_count += 1
    # 给部分帖子添加评论
    if random.random() < 0.3:
        db.add(PostComment(
            post_id=post.id,
            user_id=USER_ID,
            content=random.choice([
                "Great post! Very helpful.",
                "I agree with this approach.",
                "Thanks for sharing!",
                "Could you elaborate more?",
                "This really helped me improve.",
            ]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
        ))
db.flush()
print(f"  -> {like_count} 个点赞 + 评论")

# ============================================================
# 7. 每日任务 (daily_tasks)
# ============================================================
print("\n[7/10] 每日任务...")
task_types = ["shadowing", "conversation", "listening"]
for days_ago in range(7, -1, -1):
    n = random.randint(2, 4)
    for i in range(n):
        task_type = task_types[i % len(task_types)]
        status = random.choice(["completed", "completed", "completed", "pending"])
        db.add(DailyTask(
            user_id=USER_ID,
            task_type=task_type,
            title=f"{task_type} 练习",
            description=f"完成 {task_type} 任务",
            task_date=date.today() - timedelta(days=days_ago),
            status=status,
            score=round(random.uniform(60, 95), 1) if status == "completed" else None,
            duration_seconds=random.randint(120, 900) if status == "completed" else None,
            completed_at=datetime.utcnow() - timedelta(days=days_ago) if status == "completed" else None,
            created_at=datetime.utcnow() - timedelta(days=days_ago),
        ))
db.flush()
task_count = db.query(DailyTask).filter(DailyTask.user_id == USER_ID).count()
print(f"  -> {task_count} 条每日任务")

# ============================================================
# 8. 积分+徽章+预测
# ============================================================
print("\n[8/10] 积分+徽章+预测...")

# 积分记录
for days_ago in range(7, -1, -1):
    n = random.randint(1, 3)
    for _ in range(n):
        db.add(UserScore(
            user_id=USER_ID,
            action_type=random.choice(["daily_task", "challenge", "dubbing", "pronunciation_high", "streak"]),
            score=random.choice([10, 15, 20, 25, 30]),
            description=random.choice(["完成每日任务", "闯关成功", "配音高分", "发音练习", "连续学习"]),
            created_at=datetime.utcnow() - timedelta(days=days_ago),
        ))

# 徽章
existing_badges = {
    b.badge_type for b in db.query(UserBadge).filter(UserBadge.user_id == USER_ID).all()
}
all_badges = [
    ("newcomer", "初来乍到"),
    ("streak", "坚持之星"),
    ("pronunciation_break", "发音突破"),
    ("progress", "进步达人"),
    ("dubbing", "配音达人"),
    ("perfect", "完美发音"),
    ("scholar", "学习标兵"),
]
for badge_type, badge_name in all_badges:
    if badge_type not in existing_badges:
        db.add(UserBadge(
            user_id=USER_ID,
            badge_type=badge_type,
            badge_name=badge_name,
            awarded_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
        ))

# 预测
pred = db.query(LearningPrediction).filter(LearningPrediction.user_id == USER_ID).first()
if not pred:
    db.add(LearningPrediction(
        user_id=USER_ID,
        current_score=72.5,
        trend_slope=0.35,
        target_score=85,
        predicted_days=36,
        predicted_date=date.today() + timedelta(days=36),
    ))

db.flush()
print(f"  -> 积分/徽章/预测已补充")

# ============================================================
# 9. 通知 (notices)
# ============================================================
print("\n[9/10] 通知...")
new_notices = [
    ("achievement", "配音达人徽章", "恭喜获得「配音达人」徽章，你的配音能力正在提升！", "info", 0),
    ("alert", "连续学习提醒", "你已经连续学习 5 天，保持这个节奏！", "info", 1),
    ("prediction", "目标预测更新", "按当前进度，预计 30 天后达到目标分数 85 分", "info", 0),
    ("achievement", "闯关成功", "恭喜完成「每日单词闯关」，获得 25 积分！", "info", 0),
    ("alert", "发音提醒", "你的音素准确度有所下降，建议多练习元音发音", "warning", 0),
    ("prediction", "学习趋势", "本周 speaking 维度提升了 5 分，继续加油！", "info", 0),
    ("achievement", "社区活跃", "你在社区的讨论获得了 5 个赞！", "info", 1),
]
for typ, title, msg, level, is_read in new_notices:
    db.add(Notice(
        user_id=USER_ID,
        type=typ,
        title=title,
        message=msg,
        level=level,
        is_read=is_read,
        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23)),
    ))
db.flush()
notice_count = db.query(Notice).filter(Notice.user_id == USER_ID).count()
print(f"  -> {notice_count} 条通知")

# ============================================================
# 10. 技能分数补充 (user_skill_scores — 确保30天全覆盖)
# ============================================================
print("\n[10/10] 补充技能分数...")
dimensions = ["listening", "speaking", "reading", "grammar"]
sources = ["pronunciation", "conversation", "daily_task", "assessment"]
existing_dates = set()
skills = db.query(UserSkillScore).filter(UserSkillScore.user_id == USER_ID).all()
for s in skills:
    if s.created_at:
        existing_dates.add(s.created_at.strftime("%Y-%m-%d"))

new_scores = []
today = date.today()
for days_ago in range(30, -1, -1):
    day_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    if day_str in existing_dates:
        continue
    n = random.randint(1, 3)
    for _ in range(n):
        dim = random.choice(dimensions)
        base = 55 + (30 - days_ago) * 0.5 + random.uniform(-8, 8)
        score = round(min(98, max(30, base)), 1)
        created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(6, 22))
        new_scores.append(UserSkillScore(
            user_id=USER_ID,
            dimension=dim,
            skill_name=f"{dim}:score",
            score=score,
            source=random.choice(sources),
            created_at=created,
        ))
db.add_all(new_scores)
db.flush()
print(f"  -> 补充 {len(new_scores)} 条技能分数")

# ============================================================
# 提交
# ============================================================
db.commit()
db.close()

print("\n" + "=" * 60)
print("模拟数据生成完成！")
print(f"  发音练习: {len(pron_records)} 条")
print(f"  对话会话: {session_count} 个, 消息: {msg_count} 条")
print(f"  配音记录: {len(dubbing_records)} 条")
print(f"  语音挑战: {len(vc_submissions)} 条")
print(f"  学习资料: {len(mat_records)} 条")
print(f"  每日任务: {task_count} 条")
print(f"  通知: {notice_count} 条")
print(f"  技能分数: {len(new_scores)} 条补充")
print("=" * 60)