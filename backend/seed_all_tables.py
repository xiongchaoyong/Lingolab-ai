"""综合种子数据 — 适配 init.sql 数据库结构，为所有表填充模拟数据"""
import sys, os, random, uuid
from datetime import date, datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal

db = SessionLocal()
random.seed(42)

print("=" * 60)
print("开始生成模拟数据...")
print("=" * 60)

# ============================================================
# 1. 发音跟读内容 (pronunciation_content)
# ============================================================
print("\n[1] 发音跟读内容...")
pron_content_data = [
    ("apple", "ˈæpəl", None, "A1", "word", "/static/audio/apple.mp3"),
    ("banana", "bəˈnænə", None, "A1", "word", "/static/audio/banana.mp3"),
    ("beautiful", "ˈbjuːtɪfəl", None, "A2", "word", "/static/audio/beautiful.mp3"),
    ("computer", "kəmˈpjuːtər", None, "A2", "word", "/static/audio/computer.mp3"),
    ("elephant", "ˈelɪfənt", None, "A2", "word", "/static/audio/elephant.mp3"),
    ("Hello, how are you?", "həˈloʊ haʊ ɑːr juː", None, "A1", "sentence", "/static/audio/hello.mp3"),
    ("What time is it?", "wʌt taɪm ɪz ɪt", None, "A1", "sentence", "/static/audio/time.mp3"),
    ("I would like a cup of coffee.", "aɪ wʊd laɪk ə kʌp ʌv ˈkɔːfi", None, "A2", "sentence", "/static/audio/coffee.mp3"),
    ("Could you tell me the way to the station?", "kʊd juː tɛl miː ðə weɪ tuː ðə ˈsteɪʃən", None, "B1", "sentence", "/static/audio/station.mp3"),
    ("The weather is absolutely gorgeous today.", "ðə ˈwɛðər ɪz ˈæbsəluːtli ˈɡɔːrdʒəs təˈdeɪ", None, "B1", "sentence", "/static/audio/weather.mp3"),
    ("I have been studying English for three years.", "aɪ hæv biːn ˈstʌdiɪŋ ˈɪŋɡlɪʃ fɔːr θriː jɪrz", None, "B1", "sentence", "/static/audio/studying.mp3"),
    ("Nevertheless, we should consider all possibilities.", "ˌnɛvərðəˈlɛs wiː ʃʊd kənˈsɪdər ɔːl ˌpɑːsəˈbɪlətiz", None, "B2", "sentence", "/static/audio/nevertheless.mp3"),
]
from app.models.pronunciation import PronunciationContent
for text, ipa, phoneme, diff, mode, audio in pron_content_data:
    if db.query(PronunciationContent).filter(PronunciationContent.content_text == text).count() == 0:
        db.add(PronunciationContent(
            title=text[:30],
            content_text=text, content_type=mode, cefr_level=diff,
            category="daily", phonetic_ipa=ipa, audio_url=audio,
            tags=["core"],
        ))
db.commit()
print(f"  -> {len(pron_content_data)} 条")

# ============================================================
# 2. 测评题库 (assessment_questions) — 30题
# ============================================================
print("\n[2] 测评题库...")
from app.models.assessment import AssessmentQuestion
questions = [
    ("What does the word 'enormous' mean?", '["Very small","Very big","Very fast","Very slow"]', 2, "reading", "A2"),
    ('Choose the correct sentence:', '["He go to school.","He goes to school.","He going to school.","He gone to school."]', 2, "grammar", "A2"),
    ('What is the past tense of "eat"?', '["Eated","Ate","Eaten","Eating"]', 2, "grammar", "A2"),
    ('"She ___ to the market every Sunday."', '["go","goes","going","gone"]', 2, "grammar", "A2"),
    ('What does "grateful" mean?', '["Angry","Thankful","Sad","Tired"]', 2, "reading", "A2"),
    ('Choose the correct word: "The cat is ___ the table."', '["in","on","at","under"]', 2, "grammar", "A2"),
    ('"I have ___ finished my homework."', '["already","yet","still","just now"]', 1, "grammar", "B1"),
    ('What is the synonym of "difficult"?', '["Easy","Hard","Simple","Quick"]', 2, "reading", "B1"),
    ('"If I ___ rich, I would travel the world."', '["am","was","were","be"]', 3, "grammar", "B1"),
    ('What does "consequently" mean?', '["Before","As a result","However","In addition"]', 2, "reading", "B1"),
    ('"The book ___ by the author last year."', '["was written","is written","wrote","written"]', 1, "grammar", "B1"),
    ('"She asked me ___ I had finished the report."', '["that","if","what","which"]', 2, "grammar", "B1"),
    ('"Despite ___ tired, he continued working."', '["being","be","to be","been"]', 1, "grammar", "B2"),
    ('What does "ambiguous" mean?', '["Clear","Unclear","Obvious","Certain"]', 2, "reading", "B2"),
    ('"The project, ___ was completed on time, received praise."', '["that","which","who","what"]', 2, "grammar", "B2"),
    ('"Had I known earlier, I ___ differently."', '["would act","would have acted","will act","acted"]', 2, "grammar", "B2"),
    ('"It is imperative that he ___ the meeting."', '["attends","attend","attended","attending"]', 2, "grammar", "B2"),
    ('What is the antonym of "benevolent"?', '["Kind","Generous","Malevolent","Charitable"]', 3, "reading", "B2"),
    ('What time is it? (Listen to the audio)', '["7:30","8:00","8:30","9:00"]', 3, "listening", "A2"),
    ('Where is the conversation taking place?', '["At a restaurant","At a hotel","At a shop","At a school"]', 1, "listening", "A2"),
    ('What is the weather like today?', '["Sunny","Rainy","Cloudy","Snowy"]', 1, "listening", "A2"),
    ('What does the speaker want to order?', '["Coffee","Tea","Juice","Water"]', 1, "listening", "B1"),
    ('What is the main topic of the conversation?', '["Travel","Work","Study","Shopping"]', 1, "listening", "B1"),
    ('What is the speaker\'s opinion about the movie?', '["Positive","Negative","Neutral","Mixed"]', 1, "listening", "B1"),
    ('What is the speaker\'s purpose?', '["To inform","To persuade","To entertain","To complain"]', 2, "listening", "B2"),
    ('What can be inferred from the passage?', '["The speaker is happy","The speaker is worried","The speaker is excited","The speaker is bored"]', 2, "listening", "B2"),
    ('Describe your favorite hobby. (Speaking)', '["N/A"]', 0, "speaking", "A2"),
    ('Talk about your last vacation. (Speaking)', '["N/A"]', 0, "speaking", "B1"),
    ('Describe a person who influenced you. (Speaking)', '["N/A"]', 0, "speaking", "B1"),
    ('Discuss the pros and cons of technology in education. (Speaking)', '["N/A"]', 0, "speaking", "B2"),
]
for q_text, opts, correct, dim, diff in questions:
    if db.query(AssessmentQuestion).filter(AssessmentQuestion.question_text == q_text).count() == 0:
        db.add(AssessmentQuestion(
            question_text=q_text, options=opts, correct_option=correct,
            dimension=dim, difficulty=diff,
        ))
db.commit()
print(f"  -> 30 题")

# ============================================================
# 3. 配音内容 (dubbing_content)
# ============================================================
print("\n[3] 配音内容...")
from app.models.gamification import DubbingContent
dubbing_data = [
    ("Titanic - I'm flying", "Titanic", "easy", 10, "I'm flying, Jack!", "/static/audio/titanic.mp3"),
    ("The Lion King - Remember", "The Lion King", "easy", 8, "Remember who you are.", "/static/audio/lionking.mp3"),
    ("Forrest Gump - Life is like", "Forrest Gump", "medium", 12, "Life is like a box of chocolates.", "/static/audio/forrest.mp3"),
    ("The Dark Knight - Why so serious", "The Dark Knight", "medium", 10, "Why so serious?", "/static/audio/darkknight.mp3"),
    ("The Godfather - Offer", "The Godfather", "hard", 15, "I'm gonna make him an offer he can't refuse.", "/static/audio/godfather.mp3"),
    ("Harry Potter - Friendship", "Harry Potter", "medium", 12, "Friendship and bravery.", "/static/audio/harrypotter.mp3"),
    ("The Shawshank Redemption - Hope", "The Shawshank Redemption", "hard", 18, "Hope is a good thing, maybe the best of things.", "/static/audio/shawshank.mp3"),
    ("Frozen - Let it go", "Frozen", "easy", 10, "Let it go, let it go!", "/static/audio/frozen.mp3"),
]
for title, source, diff, dur, subtitle, audio in dubbing_data:
    if db.query(DubbingContent).filter(DubbingContent.title == title).count() == 0:
        db.add(DubbingContent(
            title=title, source=source, difficulty=diff,
            duration=dur, subtitle=subtitle, audio_url=audio,
        ))
db.commit()
print(f"  -> {len(dubbing_data)} 条")

# ============================================================
# 4. 学习资料 (learning_materials)
# ============================================================
print("\n[4] 学习资料...")
from app.models.learning import LearningMaterial
materials = [
    ("English Pronunciation Guide", "/static/materials/pron-guide.mp4", "video", "A2", "pronunciation", '["pronunciation","beginner"]', 15, None),
    ("Common English Grammar Mistakes", "/static/materials/grammar-mistakes.mp4", "video", "B1", "grammar", '["grammar","common"]', 20, None),
    ("How to Improve Your Listening Skills", "/static/materials/listening.mp4", "video", "B1", "listening", '["listening","tips"]', 18, None),
    ("Business English Vocabulary", "/static/materials/business-vocab.pdf", "article", "B2", "grammar", '["business","vocabulary"]', None, 500),
    ("English Story: The Lost Key", "/static/materials/lost-key.mp3", "audio", "A2", "listening", '["story","beginner"]', 10, None),
    ("IELTS Speaking Practice", "/static/materials/ielts-speaking.mp4", "video", "B2", "pronunciation", '["ielts","speaking"]', 25, None),
    ("Daily English Conversations", "/static/materials/daily-conv.mp3", "audio", "A2", "fluency", '["daily","conversation"]', 12, None),
    ("Advanced English Idioms", "/static/materials/idioms.pdf", "article", "B2", "grammar", '["idioms","advanced"]', None, 300),
    ("English for Travel", "/static/materials/travel.mp4", "video", "A2", "fluency", '["travel","beginner"]', 15, None),
]
for title, url, typ, diff, dim, tags, dur, wc in materials:
    if db.query(LearningMaterial).filter(LearningMaterial.title == title).count() == 0:
        db.add(LearningMaterial(
            title=title, url=url, type=typ, difficulty=diff,
            related_dimension=dim, tags=tags, duration=dur, word_count=wc,
        ))
db.commit()
print(f"  -> {len(materials)} 条")

# ============================================================
# 5. FAQ 条目
# ============================================================
print("\n[5] FAQ 条目...")
from app.models.help import FAQEntry
faqs = [
    ("How do I start a pronunciation practice?", "Click on 'Pronunciation' in the Learning Center, choose a word or sentence, and click the microphone button to record your voice.", "product_use", 10),
    ("How is my pronunciation score calculated?", "The score uses a weighted combination of phoneme accuracy (50%), stress (25%), and rhythm (25%) for words, with additional dimensions for sentences.", "product_use", 8),
    ("Can I practice without an internet connection?", "Currently, an internet connection is required for AI features and speech recognition.", "tech_issue", 5),
    ("How do I join a class?", "Go to 'My Classes' and enter the invitation code provided by your teacher.", "product_use", 7),
    ("What levels does the system support?", "The system supports CEFR levels A1 through C2, with adaptive difficulty based on your assessment results.", "study_advice", 6),
    ("How do I earn badges?", "Badges are awarded for achievements like daily streaks, high pronunciation scores, and completing challenges.", "product_use", 5),
    ("Is my data secure?", "Yes, all your data is encrypted and stored securely. We never share your personal information.", "account", 4),
    ("How can I improve my speaking fluency?", "Practice daily conversations with the AI, participate in role-play scenarios, and use the pronunciation feedback to target weak areas.", "study_advice", 9),
    ("How do I reset my password?", "Go to Profile Settings and click 'Change Password'. If you forgot your password, contact support.", "account", 3),
    ("What is the daily challenge?", "The daily challenge gives you 3-5 tasks each day, including pronunciation practice, conversations, and listening exercises.", "product_use", 6),
    ("Can I use the system on my phone?", "Yes, the web app is responsive and works on mobile browsers.", "tech_issue", 4),
]
for q, a, cat, pri in faqs:
    if db.query(FAQEntry).filter(FAQEntry.question == q).count() == 0:
        db.add(FAQEntry(question=q, answer=a, category=cat, priority=pri))
db.commit()
print(f"  -> {len(faqs)} 条")

# ============================================================
# 6. 知识图谱种子 (kg_nodes + kg_edges)
# ============================================================
print("\n[6] 知识图谱...")
from app.models.knowledge_graph import KGNode, KGEdge
if db.query(KGNode).count() == 0:
    nodes = [
        # 音素节点
        KGNode(type="phoneme", sub_type="vowel", label="/æ/", extra_data={"examples": "cat, apple"}),
        KGNode(type="phoneme", sub_type="vowel", label="/iː/", extra_data={"examples": "see, tree"}),
        KGNode(type="phoneme", sub_type="vowel", label="/ʌ/", extra_data={"examples": "cup, sun"}),
        KGNode(type="phoneme", sub_type="vowel", label="/əʊ/", extra_data={"examples": "go, home"}),
        KGNode(type="phoneme", sub_type="consonant", label="/θ/", extra_data={"examples": "think, three"}),
        KGNode(type="phoneme", sub_type="consonant", label="/ð/", extra_data={"examples": "this, that"}),
        KGNode(type="phoneme", sub_type="consonant", label="/ʃ/", extra_data={"examples": "she, fish"}),
        KGNode(type="phoneme", sub_type="consonant", label="/ŋ/", extra_data={"examples": "sing, long"}),
        # 语法节点
        KGNode(type="grammar", sub_type="tense", label="Present Simple", extra_data={"cefr": "A1"}),
        KGNode(type="grammar", sub_type="tense", label="Past Simple", extra_data={"cefr": "A2"}),
        KGNode(type="grammar", sub_type="tense", label="Present Perfect", extra_data={"cefr": "B1"}),
        KGNode(type="grammar", sub_type="tense", label="Conditionals", extra_data={"cefr": "B2"}),
        KGNode(type="grammar", sub_type="structure", label="Passive Voice", extra_data={"cefr": "B1"}),
        KGNode(type="grammar", sub_type="structure", label="Relative Clauses", extra_data={"cefr": "B2"}),
        # 场景节点
        KGNode(type="scene", sub_type="daily", label="Restaurant", extra_data={"cefr": "A2"}),
        KGNode(type="scene", sub_type="daily", label="Shopping", extra_data={"cefr": "A2"}),
        KGNode(type="scene", sub_type="daily", label="Travel", extra_data={"cefr": "B1"}),
        KGNode(type="scene", sub_type="business", label="Interview", extra_data={"cefr": "B2"}),
        KGNode(type="scene", sub_type="business", label="Meeting", extra_data={"cefr": "B2"}),
        KGNode(type="scene", sub_type="academic", label="Presentation", extra_data={"cefr": "C1"}),
    ]
    db.add_all(nodes)
    db.flush()
    # 边关系
    edges = [
        KGEdge(source_id=1, target_id=2, relation="related_to", weight=0.8),
        KGEdge(source_id=9, target_id=1, relation="uses", weight=0.9),
        KGEdge(source_id=10, target_id=5, relation="prerequisite", weight=0.7),
        KGEdge(source_id=11, target_id=10, relation="prerequisite", weight=0.8),
        KGEdge(source_id=15, target_id=9, relation="context", weight=0.6),
        KGEdge(source_id=16, target_id=9, relation="context", weight=0.6),
        KGEdge(source_id=17, target_id=11, relation="context", weight=0.7),
        KGEdge(source_id=18, target_id=14, relation="context", weight=0.8),
        KGEdge(source_id=19, target_id=14, relation="context", weight=0.8),
    ]
    db.add_all(edges)
    db.commit()
    print(f"  -> {len(nodes)} 节点 + {len(edges)} 边")
else:
    print(f"  -> 已存在，跳过")

# ============================================================
# 7. 社区数据 (语音挑战 + 讨论帖 + 学习小组)
# ============================================================
print("\n[7] 社区数据...")
from app.models.community import VoiceChallenge, ChallengeSubmission, DiscussionPost, PostComment, PostLike, StudyGroup, GroupMember
from app.models.user import UserProfile

users = db.query(UserProfile).all()
user_ids = [u.id for u in users]

# 语音挑战
if db.query(VoiceChallenge).count() == 0:
    challenges = [
        VoiceChallenge(user_id=user_ids[0], content_text="The quick brown fox jumps over the lazy dog.",
                       audio_url="/static/audio/challenge_fox.mp3", status="active",
                       expires_at=datetime.utcnow() + timedelta(days=7)),
        VoiceChallenge(user_id=user_ids[1] if len(user_ids) > 1 else user_ids[0],
                       content_text="To be or not to be, that is the question.",
                       audio_url="/static/audio/challenge_hamlet.mp3", status="active",
                       expires_at=datetime.utcnow() + timedelta(days=5)),
        VoiceChallenge(user_id=user_ids[0], content_text="Practice makes perfect.",
                       audio_url="/static/audio/challenge_practice.mp3", status="active",
                       expires_at=datetime.utcnow() + timedelta(days=3)),
    ]
    db.add_all(challenges)
    db.flush()
    print(f"  -> 3 个语音挑战")

    # 挑战提交
    for vc in [challenges[0], challenges[1]]:
        for uid in user_ids[:4]:
            db.add(ChallengeSubmission(
                challenge_id=vc.id, user_id=uid,
                audio_url=f"/static/audio/submit_{uid}_{vc.id}.mp3",
                pronunciation_score=random.randint(60, 95),
                fluency_score=random.randint(55, 90),
                total_score=random.randint(65, 92),
            ))
    print(f"  -> 挑战提交")

# 讨论帖
if db.query(DiscussionPost).count() == 0:
    posts_data = [
        (user_ids[0], "Tips for improving pronunciation", "I've been using the shadowing technique and it really helps! What methods do you use?", "learning", 150),
        (user_ids[1] if len(user_ids) > 1 else user_ids[0], "My experience with the speaking assessment", "Just completed the assessment and got B2. The feedback was very detailed.", "experience", 89),
        (user_ids[2] if len(user_ids) > 2 else user_ids[0], "Question about grammar exercises", "Does anyone know how to access the advanced grammar exercises?", "question", 45),
        (user_ids[0], "Sharing my learning routine", "I practice 30 minutes every morning. Consistency is key!", "sharing", 200),
        (user_ids[3] if len(user_ids) > 3 else user_ids[0], "Best resources for IELTS preparation", "Looking for recommendations on IELTS speaking resources.", "question", 78),
    ]
    posts = []
    for uid, title, content, cat, views in posts_data:
        posts.append(DiscussionPost(
            user_id=uid, title=title, content=content, category=cat,
            view_count=views, comment_count=0,
        ))
    db.add_all(posts)
    db.flush()
    print(f"  -> {len(posts)} 个讨论帖")

    # 评论和点赞
    comment_count = 0
    for post in posts:
        for uid in user_ids[:4]:
            if random.random() < 0.5:
                db.add(PostComment(
                    post_id=post.id, user_id=uid,
                    content=random.choice([
                        "Great post! Very helpful.",
                        "I agree with this approach.",
                        "Thanks for sharing!",
                        "Could you elaborate more?",
                        "This really helped me improve.",
                    ]),
                ))
                comment_count += 1
        db.add(PostLike(post_id=post.id, user_id=user_ids[0]))
        if len(user_ids) > 1:
            db.add(PostLike(post_id=post.id, user_id=user_ids[1]))
    db.flush()
    print(f"  -> {comment_count} 评论 + 点赞")

# 学习小组
if db.query(StudyGroup).count() == 0:
    groups = [
        StudyGroup(name="English Beginners", description="For A1-A2 learners",
                   creator_id=user_ids[0], level_range="A1-B1", max_members=20, member_count=3),
        StudyGroup(name="IELTS Preparation", description="Preparing for IELTS exam together",
                   creator_id=user_ids[1] if len(user_ids) > 1 else user_ids[0],
                   level_range="B1-C1", max_members=15, member_count=2),
        StudyGroup(name="Business English", description="Focus on workplace communication",
                   creator_id=user_ids[2] if len(user_ids) > 2 else user_ids[0],
                   level_range="B1-C2", max_members=20, member_count=2),
        StudyGroup(name="Pronunciation Club", description="Improve your accent and fluency",
                   creator_id=user_ids[0], level_range="A2-B2", max_members=25, member_count=3),
    ]
    db.add_all(groups)
    db.flush()
    # 小组成员
    member_count = 0
    for g in groups:
        for uid in user_ids[:3]:
            db.add(GroupMember(
                group_id=g.id, user_id=uid,
                role="owner" if uid == g.creator_id else "member",
            ))
            member_count += 1
    db.commit()
    print(f"  -> {len(groups)} 个小组 + {member_count} 成员")
else:
    db.commit()
    print(f"  -> 已存在，跳过")

# ============================================================
# 8. 教师/班级数据 (classes + class_students + assignments)
# ============================================================
print("\n[8] 教师/班级数据...")
from app.models.admin import Class, ClassStudent, Assignment, AssignmentSubmission
from app.models.user import UserProfile

teacher = db.query(UserProfile).filter(UserProfile.role == "teacher").first()
if not teacher:
    teacher = users[0]

if db.query(Class).count() == 0:
    classes = [
        Class(name="English 101", description="Beginner English class",
              teacher_id=teacher.id, invite_code="CLASS101", level_range="A1-A2"),
        Class(name="Intermediate Conversation", description="Practice daily conversations",
              teacher_id=teacher.id, invite_code="CONV202", level_range="B1-B2"),
        Class(name="Advanced Writing", description="Academic and business writing",
              teacher_id=teacher.id, invite_code="WRITE303", level_range="B2-C1"),
    ]
    for c in classes:
        c.invite_expires_at = datetime.utcnow() + timedelta(hours=24)
    db.add_all(classes)
    db.flush()
    print(f"  -> 3 个班级")

    # 学生加入班级
    student_users = [u for u in users if u.role == "learner"]
    for cls in classes:
        for stu in student_users[:3]:
            db.add(ClassStudent(class_id=cls.id, user_id=stu.id))
    db.flush()

    # 作业
    for cls in classes:
        for i in range(2):
            db.add(Assignment(
                class_id=cls.id, title=f"{cls.name} - Homework {i+1}",
                description=f"Practice assignment for {cls.name}",
                content_type=random.choice(["pronunciation", "conversation"]),
                content_ids=f"[{random.randint(1,5)}]",
                due_date=datetime.utcnow() + timedelta(days=random.randint(3, 14)),
            ))
    db.flush()

    # 作业提交
    assignments = db.query(Assignment).all()
    for assign in assignments:
        for stu in student_users[:2]:
            score = random.randint(60, 95)
            db.add(AssignmentSubmission(
                assignment_id=assign.id, user_id=stu.id,
                audio_url=f"/static/audio/submit_{stu.id}_{assign.id}.mp3",
                score=score,
                status=random.choice(["submitted", "reviewed"]),
                teacher_feedback="Good work!" if random.random() > 0.3 else None,
                teacher_score=score + random.randint(-5, 5) if random.random() > 0.5 else None,
            ))
    db.commit()
    print(f"  -> 作业 + 提交")
else:
    db.commit()
    print(f"  -> 已存在，跳过")

# ============================================================
# 9. 为每个用户生成积分/徽章/任务/预测/通知
# ============================================================
print("\n[9] 用户积分/徽章/任务/预测/通知...")
from app.models.gamification import UserScore, UserBadge, LearningPrediction, Notice
from app.models.knowledge_graph import DailyTask
from app.models.learning import MaterialRecord
from app.models.profile import UserSkillScore

all_badges = [
    ("newcomer", "初来乍到"), ("streak", "坚持之星"),
    ("pronunciation_break", "发音突破"), ("progress", "进步达人"),
    ("dubbing", "配音达人"), ("perfect", "完美发音"), ("scholar", "学习标兵"),
]

for user in users:
    uid = user.id
    # 积分
    for days_ago in range(14, -1, -1):
        n = random.randint(1, 3)
        for _ in range(n):
            db.add(UserScore(
                user_id=uid, action_type=random.choice(["daily_task", "challenge", "dubbing", "pronunciation_high", "streak"]),
                score=random.choice([10, 15, 20, 25, 30]),
                description=random.choice(["完成每日任务", "闯关成功", "配音高分", "发音练习", "连续学习"]),
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            ))
    # 徽章
    for badge_type, badge_name in random.sample(all_badges, random.randint(3, 7)):
        db.add(UserBadge(
            user_id=uid, badge_type=badge_type, badge_name=badge_name,
            awarded_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
        ))
    # 预测
    db.add(LearningPrediction(
        user_id=uid, current_score=round(55 + random.uniform(0, 35), 1),
        trend_slope=round(random.uniform(-0.2, 0.5), 3),
        target_score=85, predicted_days=random.randint(20, 60),
        predicted_date=date.today() + timedelta(days=random.randint(20, 60)),
    ))
    # 每日任务
    for days_ago in range(7, -1, -1):
        for i in range(random.randint(2, 4)):
            db.add(DailyTask(
                user_id=uid, task_type=random.choice(["shadowing", "conversation", "listening"]),
                title=f"{random.choice(['发音', '对话', '听力'])}练习",
                description="完成练习任务",
                task_date=date.today() - timedelta(days=days_ago),
                status=random.choice(["completed", "completed", "completed", "pending"]),
                score=round(random.uniform(60, 95), 1),
                duration_seconds=random.randint(120, 900),
                completed_at=datetime.utcnow() - timedelta(days=days_ago),
            ))
    # 通知
    notices_data = [
        ("achievement", "徽章获得", "恭喜获得新徽章！", "info", 0),
        ("alert", "学习提醒", "你已经连续学习多天，保持这个节奏！", "info", 1),
        ("prediction", "预测更新", "按当前进度，预计很快达到目标分数", "info", 0),
        ("alert", "发音提醒", "建议多练习元音发音", "warning", 0),
        ("achievement", "社区活跃", "你在社区的讨论获得了点赞！", "info", 0),
    ]
    for typ, title, msg, level, is_read in notices_data:
        db.add(Notice(
            user_id=uid, type=typ, title=title, message=msg, level=level, is_read=is_read,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
        ))
    # 技能分数
    for days_ago in range(30, -1, -3):
        for dim in ["listening", "speaking", "reading", "grammar"]:
            db.add(UserSkillScore(
                user_id=uid, dimension=dim, skill_name=f"{dim}:score",
                score=round(55 + (30 - days_ago) * 0.3 + random.uniform(-5, 5), 1),
                source=random.choice(["pronunciation", "conversation", "daily_task", "assessment"]),
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            ))

db.commit()
print(f"  -> 积分/徽章/任务/预测/通知/技能分数 已生成")

# ============================================================
# 10. 发音练习记录 + 对话记录
# ============================================================
print("\n[10] 发音练习记录 + 对话记录...")
from app.models.pronunciation import PronunciationRecord, PronunciationContent
from app.models.conversation import ConversationSession, ConversationMessage

pron_contents = db.query(PronunciationContent).all()

for user in users:
    uid = user.id
    # 发音记录
    for days_ago in range(14, -1, -1):
        if random.random() < 0.4:
            continue
        content = random.choice(pron_contents)
        score = round(60 + random.uniform(0, 35), 1)
        db.add(PronunciationRecord(
            user_id=uid, content_id=content.id,
            mode=content.content_type,
            audio_url=f"/static/audio/pron_{uid}_{content.id}_{days_ago}.wav",
            overall_score=score,
            phoneme_score=round(score * random.uniform(0.85, 1.05), 1),
            stress_score=round(score * random.uniform(0.80, 1.1), 1),
            intonation_score=round(score * random.uniform(0.75, 1.1), 1),
            rhythm_score=round(score * random.uniform(0.82, 1.08), 1),
            linking_score=round(score * random.uniform(0.78, 1.05), 1) if content.content_type == "sentence" else None,
            created_at=datetime.utcnow() - timedelta(days=days_ago),
        ))

    # 对话记录
    scenes = ["restaurant", "shopping", "self_intro", "directions"]
    for days_ago in range(10, -1, -1):
        if random.random() < 0.5:
            continue
        scene = random.choice(scenes)
        rounds = random.randint(3, 6)
        session = ConversationSession(
            user_id=uid, session_uuid=str(uuid.uuid4()),
            scene=scene, cefr_level=random.choice(["A2", "B1", "B2"]),
            round_count=rounds, status="completed",
            score_overall=round(60 + random.uniform(0, 35), 1),
            score_pronunciation=round(60 + random.uniform(0, 30), 1),
            score_grammar=round(60 + random.uniform(0, 30), 1),
            score_vocabulary=round(60 + random.uniform(0, 30), 1),
            score_engagement=round(60 + random.uniform(0, 30), 1),
            started_at=datetime.utcnow() - timedelta(days=days_ago),
            ended_at=datetime.utcnow() - timedelta(days=days_ago, minutes=rounds * 2),
        )
        db.add(session)
        db.flush()

        user_msgs = ["Hello!", "How are you?", "What do you recommend?", "Sounds great!", "Thank you!", "Goodbye!"]
        ai_msgs = ["Hi there!", "I'm doing well, thanks!", "I recommend the special.", "Glad you like it!", "You're welcome!", "Have a great day!"]
        for turn in range(rounds):
            db.add(ConversationMessage(
                session_id=session.id, round_number=turn + 1,
                role="user" if turn % 2 == 0 else "assistant",
                content_text=random.choice(user_msgs if turn % 2 == 0 else ai_msgs),
                created_at=session.started_at + timedelta(seconds=turn * 30),
            ))

db.commit()
print(f"  -> 发音/对话记录已生成")

# ============================================================
# 11. 配音记录
# ============================================================
print("\n[11] 配音记录...")
from app.models.gamification import DubbingContent, DubbingRecord
dubbing_items = db.query(DubbingContent).all()
for user in users[:4]:
    for days_ago in range(10, -1, -1):
        if random.random() < 0.5:
            continue
        item = random.choice(dubbing_items)
        score = round(55 + random.uniform(0, 40), 1)
        db.add(DubbingRecord(
            user_id=user.id, content_id=item.id,
            audio_url=f"/static/audio/dub_{user.id}_{item.id}_{days_ago}.wav",
            total_score=score,
            pronunciation_score=round(score * random.uniform(0.85, 1.1), 1),
            intonation_score=round(score * random.uniform(0.80, 1.1), 1),
            emotion_score=round(score * random.uniform(0.75, 1.1), 1),
            created_at=datetime.utcnow() - timedelta(days=days_ago),
        ))
db.commit()
print(f"  -> 配音记录已生成")

# ============================================================
# 12. 反馈数据
# ============================================================
print("\n[12] 用户反馈...")
from app.models.feedback import UserFeedback
feedbacks = [
    (users[0].id, "The pronunciation feedback is really helpful!", "feature", "pending"),
    (users[1].id if len(users) > 1 else users[0].id, "Would love to see more role-play scenarios.", "scene", "pending"),
    (users[2].id if len(users) > 2 else users[0].id, "Found a bug: the audio player sometimes doesn't play.", "bug", "pending"),
    (users[3].id if len(users) > 3 else users[0].id, "Can you add more dubbing content from movies?", "feature", "resolved"),
]
for uid, content, ftype, status in feedbacks:
    db.add(UserFeedback(user_id=uid, content=content, feedback_type=ftype, status=status,
                        admin_reply="Thanks for your feedback!" if status == "resolved" else None,
                        replied_at=datetime.utcnow() if status == "resolved" else None))
db.commit()
print(f"  -> {len(feedbacks)} 条")

# ============================================================
# 完成
# ============================================================
db.close()
print("\n" + "=" * 60)
print("模拟数据生成完成！")
print("=" * 60)