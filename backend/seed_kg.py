"""知识图谱种子数据 — 音素 + 语法 + 词汇 + 场景 + 资料节点 + 边关系"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.models.knowledge_graph import KGNode, KGEdge
from sqlalchemy import text


# ============================================================
# CEFR 等级节点
# ============================================================
CEFR_NODES = [
    {"id": "cefr:A1", "type": "cefr_level", "label": "A1 入门"},
    {"id": "cefr:A2", "type": "cefr_level", "label": "A2 基础"},
    {"id": "cefr:B1", "type": "cefr_level", "label": "B1 中级"},
    {"id": "cefr:B2", "type": "cefr_level", "label": "B2 中高级"},
    {"id": "cefr:C1", "type": "cefr_level", "label": "C1 高级"},
    {"id": "cefr:C2", "type": "cefr_level", "label": "C2 精通"},
]

# ============================================================
# 音素技能节点 (44个英语音素)
# ============================================================
PHONEME_SKILLS = [
    # 元音 Vowels
    {"id": "skill:phoneme_i", "label": "/iː/ (sheep)", "cefr": "A1",
     "similar": ["skill:phoneme_ɪ", "skill:phoneme_eɪ"]},
    {"id": "skill:phoneme_ɪ", "label": "/ɪ/ (ship)", "cefr": "A1",
     "similar": ["skill:phoneme_i", "skill:phoneme_e"]},
    {"id": "skill:phoneme_e", "label": "/e/ (bed)", "cefr": "A1",
     "similar": ["skill:phoneme_ɪ", "skill:phoneme_æ"]},
    {"id": "skill:phoneme_æ", "label": "/æ/ (cat)", "cefr": "A1",
     "similar": ["skill:phoneme_e", "skill:phoneme_ɑ"]},
    {"id": "skill:phoneme_ɑ", "label": "/ɑː/ (father)", "cefr": "A2",
     "similar": ["skill:phoneme_æ", "skill:phoneme_ʌ"]},
    {"id": "skill:phoneme_ʌ", "label": "/ʌ/ (cup)", "cefr": "A2",
     "similar": ["skill:phoneme_ɑ", "skill:phoneme_ə"]},
    {"id": "skill:phoneme_ɔ", "label": "/ɔː/ (door)", "cefr": "A2",
     "similar": ["skill:phoneme_ɒ", "skill:phoneme_oʊ"]},
    {"id": "skill:phoneme_ɒ", "label": "/ɒ/ (hot)", "cefr": "A2",
     "similar": ["skill:phoneme_ɔ", "skill:phoneme_ɑ"]},
    {"id": "skill:phoneme_u", "label": "/uː/ (food)", "cefr": "A2",
     "similar": ["skill:phoneme_ʊ", "skill:phoneme_ju"]},
    {"id": "skill:phoneme_ʊ", "label": "/ʊ/ (good)", "cefr": "A2",
     "similar": ["skill:phoneme_u", "skill:phoneme_ə"]},
    {"id": "skill:phoneme_ɜ", "label": "/ɜː/ (bird)", "cefr": "B1",
     "similar": ["skill:phoneme_ə", "skill:phoneme_ɔ"]},
    {"id": "skill:phoneme_ə", "label": "/ə/ (about)", "cefr": "B1",
     "similar": ["skill:phoneme_ʌ", "skill:phoneme_ɜ"]},
    # 双元音 Diphthongs
    {"id": "skill:phoneme_eɪ", "label": "/eɪ/ (day)", "cefr": "A1",
     "similar": ["skill:phoneme_i", "skill:phoneme_aɪ"]},
    {"id": "skill:phoneme_aɪ", "label": "/aɪ/ (my)", "cefr": "A1",
     "similar": ["skill:phoneme_eɪ", "skill:phoneme_ɔɪ"]},
    {"id": "skill:phoneme_ɔɪ", "label": "/ɔɪ/ (boy)", "cefr": "A2",
     "similar": ["skill:phoneme_aɪ", "skill:phoneme_oʊ"]},
    {"id": "skill:phoneme_aʊ", "label": "/aʊ/ (now)", "cefr": "A2",
     "similar": ["skill:phoneme_oʊ", "skill:phoneme_ɑ"]},
    {"id": "skill:phoneme_oʊ", "label": "/oʊ/ (go)", "cefr": "A1",
     "similar": ["skill:phoneme_ɔ", "skill:phoneme_aʊ"]},
    {"id": "skill:phoneme_ɪə", "label": "/ɪə/ (near)", "cefr": "B1",
     "similar": ["skill:phoneme_eə", "skill:phoneme_ɪ"]},
    {"id": "skill:phoneme_eə", "label": "/eə/ (hair)", "cefr": "B1",
     "similar": ["skill:phoneme_ɪə", "skill:phoneme_e"]},
    {"id": "skill:phoneme_ʊə", "label": "/ʊə/ (tour)", "cefr": "B2",
     "similar": ["skill:phoneme_ʊ", "skill:phoneme_u"]},
    {"id": "skill:phoneme_ju", "label": "/juː/ (university)", "cefr": "A2",
     "similar": ["skill:phoneme_u", "skill:phoneme_ʊ"]},
    # 辅音 Consonants (易错重点)
    {"id": "skill:phoneme_θ", "label": "/θ/ (think)", "cefr": "A2",
     "similar": ["skill:phoneme_ð", "skill:phoneme_s"]},
    {"id": "skill:phoneme_ð", "label": "/ð/ (this)", "cefr": "A2",
     "similar": ["skill:phoneme_θ", "skill:phoneme_d"]},
    {"id": "skill:phoneme_ʃ", "label": "/ʃ/ (she)", "cefr": "A2",
     "similar": ["skill:phoneme_ʒ", "skill:phoneme_s"]},
    {"id": "skill:phoneme_ʒ", "label": "/ʒ/ (vision)", "cefr": "B1",
     "similar": ["skill:phoneme_ʃ", "skill:phoneme_dʒ"]},
    {"id": "skill:phoneme_tʃ", "label": "/tʃ/ (church)", "cefr": "A2",
     "similar": ["skill:phoneme_dʒ", "skill:phoneme_ʃ"]},
    {"id": "skill:phoneme_dʒ", "label": "/dʒ/ (judge)", "cefr": "A2",
     "similar": ["skill:phoneme_tʃ", "skill:phoneme_ʒ"]},
    {"id": "skill:phoneme_ŋ", "label": "/ŋ/ (sing)", "cefr": "A2",
     "similar": ["skill:phoneme_n", "skill:phoneme_m"]},
    {"id": "skill:phoneme_r", "label": "/r/ (red)", "cefr": "A1",
     "similar": ["skill:phoneme_l", "skill:phoneme_w"]},
    {"id": "skill:phoneme_l", "label": "/l/ (let)", "cefr": "A1",
     "similar": ["skill:phoneme_r", "skill:phoneme_n"]},
    {"id": "skill:phoneme_v", "label": "/v/ (very)", "cefr": "A1",
     "similar": ["skill:phoneme_w", "skill:phoneme_f"]},
    {"id": "skill:phoneme_w", "label": "/w/ (we)", "cefr": "A1",
     "similar": ["skill:phoneme_v", "skill:phoneme_j"]},
    {"id": "skill:phoneme_j", "label": "/j/ (yes)", "cefr": "A1",
     "similar": ["skill:phoneme_w", "skill:phoneme_ju"]},
    {"id": "skill:phoneme_z", "label": "/z/ (zoo)", "cefr": "A1",
     "similar": ["skill:phoneme_s", "skill:phoneme_ð"]},
    {"id": "skill:phoneme_s", "label": "/s/ (sun)", "cefr": "A1",
     "similar": ["skill:phoneme_z", "skill:phoneme_θ"]},
    {"id": "skill:phoneme_f", "label": "/f/ (fan)", "cefr": "A1",
     "similar": ["skill:phoneme_v", "skill:phoneme_θ"]},
    # 基础辅音 (供 SIMILAR_TO 引用)
    {"id": "skill:phoneme_p", "label": "/p/ (pen)", "cefr": "A1", "similar": ["skill:phoneme_b"]},
    {"id": "skill:phoneme_b", "label": "/b/ (book)", "cefr": "A1", "similar": ["skill:phoneme_p"]},
    {"id": "skill:phoneme_t", "label": "/t/ (tea)", "cefr": "A1", "similar": ["skill:phoneme_d"]},
    {"id": "skill:phoneme_d", "label": "/d/ (dog)", "cefr": "A1", "similar": ["skill:phoneme_t", "skill:phoneme_ð"]},
    {"id": "skill:phoneme_k", "label": "/k/ (cat)", "cefr": "A1", "similar": ["skill:phoneme_g"]},
    {"id": "skill:phoneme_g", "label": "/g/ (go)", "cefr": "A1", "similar": ["skill:phoneme_k"]},
    {"id": "skill:phoneme_m", "label": "/m/ (man)", "cefr": "A1", "similar": ["skill:phoneme_n", "skill:phoneme_ŋ"]},
    {"id": "skill:phoneme_n", "label": "/n/ (no)", "cefr": "A1", "similar": ["skill:phoneme_m", "skill:phoneme_ŋ"]},
    {"id": "skill:phoneme_h", "label": "/h/ (hat)", "cefr": "A1", "similar": []},
]

# ============================================================
# 语法技能节点
# ============================================================
GRAMMAR_SKILLS = [
    {"id": "skill:grammar_present_simple", "label": "一般现在时", "cefr": "A1",
     "prereqs": [], "dimension": "grammar"},
    {"id": "skill:grammar_present_continuous", "label": "现在进行时", "cefr": "A1",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_past_simple", "label": "一般过去时", "cefr": "A1",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_future_will", "label": "将来时 will", "cefr": "A2",
     "prereqs": ["skill:grammar_present_simple", "skill:grammar_present_continuous"], "dimension": "grammar"},
    {"id": "skill:grammar_future_going_to", "label": "将来时 be going to", "cefr": "A2",
     "prereqs": ["skill:grammar_present_continuous"], "dimension": "grammar"},
    {"id": "skill:grammar_present_perfect", "label": "现在完成时", "cefr": "B1",
     "prereqs": ["skill:grammar_past_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_past_continuous", "label": "过去进行时", "cefr": "B1",
     "prereqs": ["skill:grammar_past_simple", "skill:grammar_present_continuous"], "dimension": "grammar"},
    {"id": "skill:grammar_past_perfect", "label": "过去完成时", "cefr": "B2",
     "prereqs": ["skill:grammar_present_perfect", "skill:grammar_past_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_conditionals_1", "label": "第一条件句", "cefr": "B1",
     "prereqs": ["skill:grammar_present_simple", "skill:grammar_future_will"], "dimension": "grammar"},
    {"id": "skill:grammar_conditionals_2", "label": "第二条件句", "cefr": "B2",
     "prereqs": ["skill:grammar_conditionals_1", "skill:grammar_past_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_conditionals_3", "label": "第三条件句", "cefr": "C1",
     "prereqs": ["skill:grammar_conditionals_2", "skill:grammar_past_perfect"], "dimension": "grammar"},
    {"id": "skill:grammar_passive_voice", "label": "被动语态", "cefr": "B1",
     "prereqs": ["skill:grammar_past_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_relative_clauses", "label": "关系从句", "cefr": "B2",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_modal_can", "label": "情态动词 can/could", "cefr": "A2",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_modal_must", "label": "情态动词 must/should", "cefr": "B1",
     "prereqs": ["skill:grammar_modal_can"], "dimension": "grammar"},
    {"id": "skill:grammar_articles", "label": "冠词 a/an/the", "cefr": "A1",
     "prereqs": [], "dimension": "grammar"},
    {"id": "skill:grammar_prepositions", "label": "介词搭配", "cefr": "A2",
     "prereqs": [], "dimension": "grammar"},
    {"id": "skill:grammar_comparatives", "label": "比较级与最高级", "cefr": "A2",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_gerunds", "label": "动名词与不定式", "cefr": "B1",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
    {"id": "skill:grammar_reported_speech", "label": "间接引语", "cefr": "B2",
     "prereqs": ["skill:grammar_past_simple", "skill:grammar_past_perfect"], "dimension": "grammar"},
    {"id": "skill:grammar_question_tags", "label": "反意疑问句", "cefr": "B1",
     "prereqs": ["skill:grammar_present_simple"], "dimension": "grammar"},
]

# ============================================================
# 词汇技能节点
# ============================================================
VOCABULARY_SKILLS = [
    {"id": "skill:vocab_food", "label": "食物与餐饮", "cefr": "A1", "topics": ["topic:restaurant"]},
    {"id": "skill:vocab_family", "label": "家庭与人物", "cefr": "A1", "topics": ["topic:self_introduction"]},
    {"id": "skill:vocab_daily", "label": "日常生活", "cefr": "A1", "topics": ["topic:self_introduction"]},
    {"id": "skill:vocab_travel", "label": "旅行与交通", "cefr": "A2", "topics": ["topic:travel"]},
    {"id": "skill:vocab_shopping", "label": "购物与消费", "cefr": "A2", "topics": ["topic:shopping"]},
    {"id": "skill:vocab_health", "label": "健康与医疗", "cefr": "B1", "topics": ["topic:health"]},
    {"id": "skill:vocab_business", "label": "商务与职场", "cefr": "B1", "topics": ["topic:job_interview"]},
    {"id": "skill:vocab_technology", "label": "科技与互联网", "cefr": "B1", "topics": ["topic:technology"]},
    {"id": "skill:vocab_education", "label": "教育与学术", "cefr": "B2", "topics": ["topic:education"]},
    {"id": "skill:vocab_environment", "label": "环境与气候", "cefr": "B2", "topics": ["topic:environment"]},
    {"id": "skill:vocab_culture", "label": "文化与艺术", "cefr": "B2", "topics": ["topic:culture"]},
    {"id": "skill:vocab_emotion", "label": "情感与心理", "cefr": "B1", "topics": ["topic:self_introduction"]},
]

# ============================================================
# 场景/话题节点
# ============================================================
TOPIC_NODES = [
    {"id": "topic:self_introduction", "label": "自我介绍与日常问候", "cefr": "A1",
     "scene": "self_intro", "tags": ["日常", "社交"]},
    {"id": "topic:restaurant", "label": "餐厅点餐", "cefr": "A2",
     "scene": "restaurant", "tags": ["美食", "日常"]},
    {"id": "topic:shopping", "label": "购物消费", "cefr": "A2",
     "scene": "shopping", "tags": ["购物", "日常"]},
    {"id": "topic:travel", "label": "旅行交通", "cefr": "A2",
     "scene": "directions", "tags": ["旅行", "交通"]},
    {"id": "topic:hotel", "label": "酒店入住", "cefr": "A2",
     "scene": "hotel", "tags": ["旅行", "住宿"]},
    {"id": "topic:airport", "label": "机场值机", "cefr": "A2",
     "scene": "airport", "tags": ["旅行", "交通"]},
    {"id": "topic:health", "label": "看病就医", "cefr": "B1",
     "scene": "hospital", "tags": ["健康", "医疗"]},
    {"id": "topic:job_interview", "label": "工作面试", "cefr": "B2",
     "scene": "interviewee", "tags": ["商务", "职场"]},
    {"id": "topic:business_meeting", "label": "商务会议", "cefr": "C1",
     "scene": "business", "tags": ["商务", "职场"]},
    {"id": "topic:technology", "label": "科技话题讨论", "cefr": "B1",
     "scene": "technology", "tags": ["科技", "学术"]},
    {"id": "topic:education", "label": "教育与留学", "cefr": "B2",
     "scene": "education", "tags": ["教育", "学术"]},
    {"id": "topic:environment", "label": "环境保护", "cefr": "B2",
     "scene": "environment", "tags": ["环境", "社会"]},
    {"id": "topic:culture", "label": "文化差异讨论", "cefr": "B2",
     "scene": "culture", "tags": ["文化", "社会"]},
    {"id": "topic:entertainment", "label": "娱乐休闲", "cefr": "A2",
     "scene": "entertainment", "tags": ["娱乐", "音乐", "电影"]},
    {"id": "topic:academic_presentation", "label": "学术演讲", "cefr": "C1",
     "scene": "academic", "tags": ["学术", "教育"]},
]

# ============================================================
# 资料节点 (素材内容)
# ============================================================
MATERIAL_NODES = [
    # 视频 (10条)
    {"id": "material:video_1", "type": "material", "sub_type": "video",
     "label": "Master English TH Sound", "url": "https://youtube.com/example/th-sound",
     "difficulty": "A2", "duration": "5分钟", "teaches": ["skill:phoneme_θ", "skill:phoneme_ð"],
     "covers": [], "tags": ["发音", "音素"]},
    {"id": "material:video_2", "type": "material", "sub_type": "video",
     "label": "Speak Naturally in 30 Days", "url": "https://youtube.com/example/natural-speech",
     "difficulty": "B1", "duration": "10分钟", "teaches": ["skill:phoneme_eɪ", "skill:phoneme_oʊ", "skill:phoneme_ə"],
     "covers": ["topic:self_introduction"], "tags": ["发音", "流利度"]},
    {"id": "material:video_3", "type": "material", "sub_type": "video",
     "label": "Business English: Meeting Expressions", "url": "https://youtube.com/example/business-meeting",
     "difficulty": "B2", "duration": "8分钟", "teaches": ["skill:grammar_modal_must"],
     "covers": ["topic:business_meeting"], "tags": ["商务", "职场"]},
    {"id": "material:video_4", "type": "material", "sub_type": "video",
     "label": "English R and L Pronunciation", "url": "https://youtube.com/example/rl-sounds",
     "difficulty": "A1", "duration": "4分钟", "teaches": ["skill:phoneme_r", "skill:phoneme_l"],
     "covers": [], "tags": ["发音", "音素"]},
    {"id": "material:video_5", "type": "material", "sub_type": "video",
     "label": "Ordering Food in English", "url": "https://youtube.com/example/ordering-food",
     "difficulty": "A2", "duration": "6分钟", "teaches": ["skill:vocab_food"],
     "covers": ["topic:restaurant"], "tags": ["日常", "美食"]},
    {"id": "material:video_6", "type": "material", "sub_type": "video",
     "label": "Job Interview Tips", "url": "https://youtube.com/example/job-interview",
     "difficulty": "B2", "duration": "10分钟", "teaches": ["skill:vocab_business", "skill:grammar_conditionals_2"],
     "covers": ["topic:job_interview"], "tags": ["商务", "职场"]},
    {"id": "material:video_7", "type": "material", "sub_type": "video",
     "label": "Past Tense Mastery", "url": "https://youtube.com/example/past-tense",
     "difficulty": "A1", "duration": "5分钟", "teaches": ["skill:grammar_past_simple"],
     "covers": [], "tags": ["语法"]},
    {"id": "material:video_8", "type": "material", "sub_type": "video",
     "label": "Travel English Essentials", "url": "https://youtube.com/example/travel",
     "difficulty": "A2", "duration": "7分钟", "teaches": ["skill:vocab_travel"],
     "covers": ["topic:travel", "topic:airport"], "tags": ["旅行", "日常"]},
    {"id": "material:video_9", "type": "material", "sub_type": "video",
     "label": "Present Perfect Explained", "url": "https://youtube.com/example/present-perfect",
     "difficulty": "B1", "duration": "8分钟", "teaches": ["skill:grammar_present_perfect"],
     "covers": [], "tags": ["语法"]},
    {"id": "material:video_10", "type": "material", "sub_type": "video",
     "label": "Shopping Dialogue Practice", "url": "https://youtube.com/example/shopping",
     "difficulty": "A2", "duration": "5分钟", "teaches": ["skill:vocab_shopping"],
     "covers": ["topic:shopping"], "tags": ["购物", "日常"]},
    # 文章 (10条)
    {"id": "material:article_1", "type": "material", "sub_type": "article",
     "label": "The History of English Language", "url": "https://example.com/english-history",
     "difficulty": "B1", "duration": "400词", "teaches": [],
     "covers": ["topic:culture"], "tags": ["文化", "历史"]},
    {"id": "material:article_2", "type": "material", "sub_type": "article",
     "label": "Tips for Job Interviews", "url": "https://example.com/job-tips",
     "difficulty": "B2", "duration": "350词", "teaches": ["skill:vocab_business"],
     "covers": ["topic:job_interview"], "tags": ["商务", "职场"]},
    {"id": "material:article_3", "type": "material", "sub_type": "article",
     "label": "Climate Change: A Global Challenge", "url": "https://example.com/climate",
     "difficulty": "B2", "duration": "500词", "teaches": ["skill:vocab_environment"],
     "covers": ["topic:environment"], "tags": ["环境", "社会"]},
    {"id": "material:article_4", "type": "material", "sub_type": "article",
     "label": "My Daily Routine", "url": "https://example.com/daily-routine",
     "difficulty": "A1", "duration": "200词", "teaches": ["skill:vocab_daily", "skill:grammar_present_simple"],
     "covers": [], "tags": ["日常"]},
    {"id": "material:article_5", "type": "material", "sub_type": "article",
     "label": "The Future of AI Technology", "url": "https://example.com/ai-future",
     "difficulty": "C1", "duration": "500词", "teaches": ["skill:vocab_technology"],
     "covers": ["topic:technology"], "tags": ["科技", "学术"]},
    {"id": "material:article_6", "type": "material", "sub_type": "article",
     "label": "How to Stay Healthy", "url": "https://example.com/health-tips",
     "difficulty": "B1", "duration": "300词", "teaches": ["skill:vocab_health"],
     "covers": ["topic:health"], "tags": ["健康", "生活"]},
    {"id": "material:article_7", "type": "material", "sub_type": "article",
     "label": "A Wonderful Trip to London", "url": "https://example.com/london-trip",
     "difficulty": "A2", "duration": "250词", "teaches": ["skill:vocab_travel", "skill:grammar_past_simple"],
     "covers": ["topic:travel"], "tags": ["旅行", "文化"]},
    {"id": "material:article_8", "type": "material", "sub_type": "article",
     "label": "Studying Abroad: Pros and Cons", "url": "https://example.com/study-abroad",
     "difficulty": "B2", "duration": "450词", "teaches": ["skill:vocab_education"],
     "covers": ["topic:education"], "tags": ["教育", "旅行"]},
    {"id": "material:article_9", "type": "material", "sub_type": "article",
     "label": "Modern Art Movements", "url": "https://example.com/modern-art",
     "difficulty": "B2", "duration": "400词", "teaches": ["skill:vocab_culture"],
     "covers": ["topic:culture"], "tags": ["文化", "艺术"]},
    {"id": "material:article_10", "type": "material", "sub_type": "article",
     "label": "A Letter to My Friend", "url": "https://example.com/letter-friend",
     "difficulty": "A1", "duration": "180词", "teaches": ["skill:vocab_daily", "skill:grammar_present_continuous"],
     "covers": [], "tags": ["日常", "社交"]},
    # 音频 (10条)
    {"id": "material:audio_1", "type": "material", "sub_type": "audio",
     "label": "Ordering at a Restaurant", "url": "https://example.com/audio/restaurant",
     "difficulty": "A2", "duration": "4分钟", "teaches": ["skill:vocab_food"],
     "covers": ["topic:restaurant"], "tags": ["日常", "美食"]},
    {"id": "material:audio_2", "type": "material", "sub_type": "audio",
     "label": "Daily English Conversations", "url": "https://example.com/audio/daily",
     "difficulty": "A1", "duration": "5分钟", "teaches": ["skill:vocab_daily"],
     "covers": ["topic:self_introduction"], "tags": ["日常", "社交"]},
    {"id": "material:audio_3", "type": "material", "sub_type": "audio",
     "label": "Business Phone Call", "url": "https://example.com/audio/business-phone",
     "difficulty": "B1", "duration": "6分钟", "teaches": ["skill:vocab_business"],
     "covers": ["topic:business_meeting"], "tags": ["商务", "职场"]},
    {"id": "material:audio_4", "type": "material", "sub_type": "audio",
     "label": "At the Airport", "url": "https://example.com/audio/airport",
     "difficulty": "A2", "duration": "3分钟", "teaches": ["skill:vocab_travel"],
     "covers": ["topic:airport"], "tags": ["旅行", "交通"]},
    {"id": "material:audio_5", "type": "material", "sub_type": "audio",
     "label": "BBC News: Technology", "url": "https://example.com/audio/bbc-tech",
     "difficulty": "B2", "duration": "5分钟", "teaches": ["skill:vocab_technology"],
     "covers": ["topic:technology"], "tags": ["科技", "新闻"]},
    {"id": "material:audio_6", "type": "material", "sub_type": "audio",
     "label": "Shopping for Clothes", "url": "https://example.com/audio/shopping",
     "difficulty": "A2", "duration": "4分钟", "teaches": ["skill:vocab_shopping"],
     "covers": ["topic:shopping"], "tags": ["购物", "日常"]},
    {"id": "material:audio_7", "type": "material", "sub_type": "audio",
     "label": "ESL Podcast: Health", "url": "https://example.com/audio/esl-health",
     "difficulty": "B1", "duration": "8分钟", "teaches": ["skill:vocab_health"],
     "covers": ["topic:health"], "tags": ["健康", "生活"]},
    {"id": "material:audio_8", "type": "material", "sub_type": "audio",
     "label": "Academic Lecture: Climate", "url": "https://example.com/audio/lecture-climate",
     "difficulty": "C1", "duration": "10分钟", "teaches": ["skill:vocab_environment"],
     "covers": ["topic:environment"], "tags": ["学术", "环境"]},
    {"id": "material:audio_9", "type": "material", "sub_type": "audio",
     "label": "Movie Discussion Podcast", "url": "https://example.com/audio/movie",
     "difficulty": "B1", "duration": "7分钟", "teaches": [],
     "covers": ["topic:entertainment"], "tags": ["娱乐", "电影"]},
    {"id": "material:audio_10", "type": "material", "sub_type": "audio",
     "label": "Job Interview Role Play", "url": "https://example.com/audio/interview",
     "difficulty": "B2", "duration": "6分钟", "teaches": ["skill:vocab_business"],
     "covers": ["topic:job_interview"], "tags": ["商务", "职场"]},
]


def seed():
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(KGNode).count()
        if existing > 0:
            print(f"知识图谱已有 {existing} 个节点，跳过种子数据")
            return

        # 清空重插
        db.execute(text("DELETE FROM kg_edges"))
        db.execute(text("DELETE FROM kg_nodes"))
        db.commit()

        node_count = 0
        edge_count = 0

        # ========== 阶段 1：插入所有节点 ==========

        # CEFR 等级节点
        for n in CEFR_NODES:
            db.add(KGNode(id=n["id"], type=n["type"], label=n["label"]))
            node_count += 1
        db.flush()

        # 音素技能节点
        for p in PHONEME_SKILLS:
            db.add(KGNode(
                id=p["id"], type="skill", sub_type="phoneme",
                label=p["label"],
                extra_data={"cefr": p["cefr"], "similar": p.get("similar", [])}
            ))
            node_count += 1
        db.flush()

        # 语法技能节点
        for g in GRAMMAR_SKILLS:
            db.add(KGNode(
                id=g["id"], type="skill", sub_type="grammar",
                label=g["label"],
                extra_data={"cefr": g["cefr"], "dimension": g["dimension"]}
            ))
            node_count += 1
        db.flush()

        # 词汇技能节点
        for v in VOCABULARY_SKILLS:
            db.add(KGNode(
                id=v["id"], type="skill", sub_type="vocabulary",
                label=v["label"],
                extra_data={"cefr": v["cefr"]}
            ))
            node_count += 1
        db.flush()

        # 场景节点
        for t in TOPIC_NODES:
            db.add(KGNode(
                id=t["id"], type="topic", sub_type="scene",
                label=t["label"],
                extra_data={"scene": t["scene"], "tags": t["tags"]}
            ))
            node_count += 1
        db.flush()

        # 资料节点
        for m in MATERIAL_NODES:
            db.add(KGNode(
                id=m["id"], type="material", sub_type=m["sub_type"],
                label=m["label"],
                extra_data={
                    "url": m["url"],
                    "difficulty": m["difficulty"],
                    "duration": m["duration"],
                    "tags": m["tags"],
                }
            ))
            node_count += 1
        db.flush()

        print(f"阶段 1 完成：{node_count} 个节点已写入")

        # ========== 阶段 2：插入所有边 ==========

        # 音素边：BELONGS_TO + SIMILAR_TO
        for p in PHONEME_SKILLS:
            db.add(KGEdge(source_id=p["id"], target_id=f"cefr:{p['cefr']}", relation="BELONGS_TO"))
            edge_count += 1
            for sim_id in p.get("similar", []):
                db.add(KGEdge(source_id=p["id"], target_id=sim_id, relation="SIMILAR_TO", weight=0.7))
                edge_count += 1

        # 语法边：BELONGS_TO + HAS_PREREQ
        for g in GRAMMAR_SKILLS:
            db.add(KGEdge(source_id=g["id"], target_id=f"cefr:{g['cefr']}", relation="BELONGS_TO"))
            edge_count += 1
            for prereq_id in g.get("prereqs", []):
                db.add(KGEdge(source_id=g["id"], target_id=prereq_id, relation="HAS_PREREQ", weight=0.8))
                edge_count += 1

        # 词汇边：BELONGS_TO
        for v in VOCABULARY_SKILLS:
            db.add(KGEdge(source_id=v["id"], target_id=f"cefr:{v['cefr']}", relation="BELONGS_TO"))
            edge_count += 1

        # 场景边：BELONGS_TO
        for t in TOPIC_NODES:
            db.add(KGEdge(source_id=t["id"], target_id=f"cefr:{t['cefr']}", relation="BELONGS_TO"))
            edge_count += 1

        # 资料边：BELONGS_TO + TEACHES + COVERS
        for m in MATERIAL_NODES:
            db.add(KGEdge(source_id=m["id"], target_id=f"cefr:{m['difficulty']}", relation="BELONGS_TO"))
            edge_count += 1
            for skill_id in m.get("teaches", []):
                db.add(KGEdge(source_id=m["id"], target_id=skill_id, relation="TEACHES", weight=0.9))
                edge_count += 1
            for topic_id in m.get("covers", []):
                db.add(KGEdge(source_id=m["id"], target_id=topic_id, relation="COVERS", weight=0.8))
                edge_count += 1

        db.commit()
        print(f"阶段 2 完成：{edge_count} 条边已写入")
        print(f"总计：{node_count} 个节点, {edge_count} 条边")

    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()