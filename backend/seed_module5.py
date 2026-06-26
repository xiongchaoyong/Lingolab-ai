"""模块5 种子数据 — 语音挑战/讨论帖/学习小组"""

from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import UserProfile  # noqa: 确保关系引用可用
from app.models.community import (
    VoiceChallenge,
    ChallengeSubmission,
    DiscussionPost,
    PostComment,
    StudyGroup,
    GroupMember,
)

db = SessionLocal()

# ============================================================
# 1. 语音挑战
# ============================================================
challenges = [
    VoiceChallenge(
        title="Tongue Twister Challenge",
        description="挑战绕口令，看看谁的发音最标准！",
        sample_text="She sells seashells by the seashore. The shells she sells are surely seashells.",
        deadline=datetime.utcnow() + timedelta(days=7),
        is_active=True,
    ),
    VoiceChallenge(
        title="BBC News Shadow Reading",
        description="跟读 BBC 新闻片段，练习英式发音和语调",
        sample_text="The government has announced new measures to tackle climate change, including a ban on petrol cars by 2030.",
        deadline=datetime.utcnow() + timedelta(days=5),
        is_active=True,
    ),
    VoiceChallenge(
        title="Poem Recitation",
        description="朗诵经典英文诗歌，展现你的语音韵律感",
        sample_text="Shall I compare thee to a summer's day? Thou art more lovely and more temperate.",
        deadline=datetime.utcnow() + timedelta(days=3),
        is_active=True,
    ),
]
db.add_all(challenges)
db.flush()
print(f"Inserted {len(challenges)} voice challenges")

# ============================================================
# 2. 讨论帖
# ============================================================
posts = [
    DiscussionPost(
        user_id=4,
        topic="What is the best way to improve English speaking fluency?",
        content="I think the key is consistent practice every day. Even 15 minutes of speaking out loud makes a huge difference. I've been doing shadow reading for 3 months and my fluency improved a lot.",
        likes_count=5,
        comments_count=2,
        created_at=datetime.utcnow() - timedelta(hours=2),
        updated_at=datetime.utcnow() - timedelta(hours=2),
    ),
    DiscussionPost(
        user_id=8,
        topic="Tips for reducing accent in English?",
        content="Shadow reading has been the most effective method for me. I listen to BBC podcasts and repeat after the speaker. Also recording myself and comparing with native speakers helps a lot.",
        likes_count=3,
        comments_count=1,
        created_at=datetime.utcnow() - timedelta(hours=5),
        updated_at=datetime.utcnow() - timedelta(hours=5),
    ),
    DiscussionPost(
        user_id=3,
        topic="How to prepare for IELTS speaking test?",
        content="Focus on coherence and fluency first. Many students worry too much about vocabulary but forget about natural flow. Practice with a timer and record yourself to review later.",
        likes_count=7,
        comments_count=3,
        created_at=datetime.utcnow() - timedelta(days=1),
        updated_at=datetime.utcnow() - timedelta(days=1),
    ),
]
db.add_all(posts)
db.flush()
print(f"Inserted {len(posts)} discussion posts")

# ============================================================
# 3. 评论
# ============================================================
comments = [
    PostComment(post_id=posts[0].id, user_id=8, content="Totally agree! Consistency is key. I also recommend using language exchange apps.", created_at=datetime.utcnow() - timedelta(hours=1)),
    PostComment(post_id=posts[0].id, user_id=3, content="Shadow reading is great. I've been doing it for 6 months now.", created_at=datetime.utcnow() - timedelta(minutes=30)),
    PostComment(post_id=posts[1].id, user_id=4, content="BBC podcasts are excellent for learning British pronunciation.", created_at=datetime.utcnow() - timedelta(hours=3)),
    PostComment(post_id=posts[2].id, user_id=4, content="Great advice! I think part 2 is the hardest, any tips for that?", created_at=datetime.utcnow() - timedelta(hours=12)),
    PostComment(post_id=posts[2].id, user_id=8, content="For part 2, practice the 1-minute preparation strategy. Write down keywords, not full sentences.", created_at=datetime.utcnow() - timedelta(hours=10)),
    PostComment(post_id=posts[2].id, user_id=3, content="Also don't forget to use discourse markers naturally - they help with coherence score.", created_at=datetime.utcnow() - timedelta(hours=8)),
]
db.add_all(comments)
db.flush()
print(f"Inserted {len(comments)} comments")

# ============================================================
# 4. 学习小组
# ============================================================
groups = [
    StudyGroup(
        name="Daily Speaking Club",
        description="每天练习口语，互相纠正发音和语法",
        creator_id=4,
        level_range="B1",
        schedule="每天晚上 20:00",
        tags="口语,日常",
        member_count=1,
        is_archived=False,
    ),
    StudyGroup(
        name="IELTS Prep Squad",
        description="雅思备考小组，分享考试技巧和模拟练习",
        creator_id=4,
        level_range="B2",
        schedule="周二/周四 19:30",
        tags="雅思,备考",
        member_count=0,
        is_archived=False,
    ),
    StudyGroup(
        name="Pronunciation Lab",
        description="专注发音训练，使用音标和最小对立体练习",
        creator_id=4,
        level_range="A2",
        schedule="周一/三/五 18:00",
        tags="发音,纠音",
        member_count=0,
        is_archived=False,
    ),
    StudyGroup(
        name="Business English",
        description="职场英语，涵盖会议/邮件/演讲等场景",
        creator_id=4,
        level_range="B2",
        schedule="周六 10:00",
        tags="商务,职场",
        member_count=0,
        is_archived=False,
    ),
]
db.add_all(groups)
db.flush()
print(f"Inserted {len(groups)} study groups")

# 用户4加入第一个小组
db.add(GroupMember(group_id=groups[0].id, user_id=4))
db.flush()
print("User 4 joined Daily Speaking Club")

db.commit()
db.close()
print("\nModule 5 seed data inserted successfully!")