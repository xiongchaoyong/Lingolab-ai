"""种子数据 — 发音内容库 / 配音内容 / 学习资料 / FAQ 条目

用法：cd backend && python seed_content.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.pronunciation import PronunciationContent
from app.models.gamification import DubbingContent
from app.models.learning import LearningMaterial
from app.models.support import FAQEntry


def seed_pronunciation_content(db):
    """跟读内容库 — 单词 + 句子，覆盖 A1-C2"""
    items = [
        # A1 单词
        {"title": "基础问候", "content_text": "hello", "content_type": "word", "cefr_level": "A1", "category": "日常", "phonetic_ipa": "/həˈloʊ/"},
        {"title": "感谢", "content_text": "thank you", "content_type": "word", "cefr_level": "A1", "category": "日常", "phonetic_ipa": "/θæŋk juː/"},
        {"title": "请", "content_text": "please", "content_type": "word", "cefr_level": "A1", "category": "日常", "phonetic_ipa": "/pliːz/"},
        {"title": "对不起", "content_text": "sorry", "content_type": "word", "cefr_level": "A1", "category": "日常", "phonetic_ipa": "/ˈsɒri/"},
        {"title": "水", "content_text": "water", "content_type": "word", "cefr_level": "A1", "category": "日常", "phonetic_ipa": "/ˈwɔːtər/"},
        # A2 单词
        {"title": "美丽的", "content_text": "beautiful", "content_type": "word", "cefr_level": "A2", "category": "形容词", "phonetic_ipa": "/ˈbjuːtɪfəl/"},
        {"title": "重要的", "content_text": "important", "content_type": "word", "cefr_level": "A2", "category": "形容词", "phonetic_ipa": "/ɪmˈpɔːrtənt/"},
        {"title": "经验", "content_text": "experience", "content_type": "word", "cefr_level": "A2", "category": "名词", "phonetic_ipa": "/ɪkˈspɪəriəns/"},
        # B1 单词
        {"title": "成就", "content_text": "achievement", "content_type": "word", "cefr_level": "B1", "category": "名词", "phonetic_ipa": "/əˈtʃiːvmənt/"},
        {"title": "环境", "content_text": "environment", "content_type": "word", "cefr_level": "B1", "category": "名词", "phonetic_ipa": "/ɪnˈvaɪrənmənt/"},
        {"title": "机会", "content_text": "opportunity", "content_type": "word", "cefr_level": "B1", "category": "名词", "phonetic_ipa": "/ˌɒpəˈtjuːnɪti/"},
        # B2 单词
        {"title": "可持续的", "content_text": "sustainable", "content_type": "word", "cefr_level": "B2", "category": "形容词", "phonetic_ipa": "/səˈsteɪnəbl/"},
        {"title": "复杂性", "content_text": "complexity", "content_type": "word", "cefr_level": "B2", "category": "名词", "phonetic_ipa": "/kəmˈpleksɪti/"},
        # A1 句子
        {"title": "自我介绍", "content_text": "My name is Tom. I am from China.", "content_type": "sentence", "cefr_level": "A1", "category": "日常"},
        {"title": "询问时间", "content_text": "What time is it now?", "content_type": "sentence", "cefr_level": "A1", "category": "日常"},
        # A2 句子
        {"title": "描述天气", "content_text": "The weather is nice today. Let's go for a walk.", "content_type": "sentence", "cefr_level": "A2", "category": "日常"},
        {"title": "点餐", "content_text": "I would like a cup of coffee and a sandwich, please.", "content_type": "sentence", "cefr_level": "A2", "category": "餐厅"},
        # B1 句子
        {"title": "表达观点", "content_text": "I believe that learning a new language opens up many opportunities.", "content_type": "sentence", "cefr_level": "B1", "category": "观点"},
        {"title": "商务会议", "content_text": "Could we schedule a meeting to discuss the project timeline?", "content_type": "sentence", "cefr_level": "B1", "category": "商务"},
        # B2 句子
        {"title": "学术讨论", "content_text": "The research findings suggest a significant correlation between practice frequency and pronunciation improvement.", "content_type": "sentence", "cefr_level": "B2", "category": "学术"},
        {"title": "复杂表达", "content_text": "Despite the challenges we faced, the team managed to deliver the project ahead of schedule.", "content_type": "sentence", "cefr_level": "B2", "category": "商务"},
    ]
    for item in items:
        db.add(PronunciationContent(**item))
    print(f"  ✓ 发音内容库：{len(items)} 条")


def seed_dubbing_content(db):
    """配音内容库 — 影视经典片段"""
    items = [
        {"title": "狮子王 - Remember who you are", "source": "The Lion King", "difficulty": "easy", "duration": 8, "subtitle": "Remember who you are. You are my son, and the one true king.", "audio_url": "/audio/dubbing/lion_king.mp3"},
        {"title": "冰雪奇缘 - Let it go", "source": "Frozen", "difficulty": "easy", "duration": 10, "subtitle": "Let it go, let it go. Can't hold it back anymore.", "audio_url": "/audio/dubbing/frozen.mp3"},
        {"title": "阿甘正传 - Life is like a box of chocolates", "source": "Forrest Gump", "difficulty": "easy", "duration": 12, "subtitle": "My mama always said, life is like a box of chocolates. You never know what you're gonna get.", "audio_url": "/audio/dubbing/forrest_gump.mp3"},
        {"title": "泰坦尼克号 - I'm the king of the world", "source": "Titanic", "difficulty": "easy", "duration": 6, "subtitle": "I'm the king of the world!", "audio_url": "/audio/dubbing/titanic.mp3"},
        {"title": "哈利波特 - Yer a wizard", "source": "Harry Potter", "difficulty": "medium", "duration": 10, "subtitle": "You're a wizard, Harry. You're a wizard.", "audio_url": "/audio/dubbing/harry_potter.mp3"},
        {"title": "蜘蛛侠 - With great power", "source": "Spider-Man", "difficulty": "medium", "duration": 8, "subtitle": "With great power comes great responsibility.", "audio_url": "/audio/dubbing/spider_man.mp3"},
        {"title": "当幸福来敲门 - Don't let somebody tell you", "source": "The Pursuit of Happyness", "difficulty": "medium", "duration": 15, "subtitle": "Don't ever let somebody tell you you can't do something. Not even me.", "audio_url": "/audio/dubbing/pursuit.mp3"},
        {"title": "肖申克的救赎 - Hope is a good thing", "source": "The Shawshank Redemption", "difficulty": "hard", "duration": 12, "subtitle": "Hope is a good thing, maybe the best of things, and no good thing ever dies.", "audio_url": "/audio/dubbing/shawshank.mp3"},
        {"title": "星际穿越 - Do not go gentle", "source": "Interstellar", "difficulty": "hard", "duration": 14, "subtitle": "Do not go gentle into that good night. Rage, rage against the dying of the light.", "audio_url": "/audio/dubbing/interstellar.mp3"},
        {"title": "国王的演讲 - The speech", "source": "The King's Speech", "difficulty": "hard", "duration": 18, "subtitle": "In this grave hour, perhaps the most fateful in history, I send to every household of my peoples, both at home and overseas, this message.", "audio_url": "/audio/dubbing/kings_speech.mp3"},
    ]
    for item in items:
        db.add(DubbingContent(**item))
    print(f"  ✓ 配音内容库：{len(items)} 条")


def seed_learning_materials(db):
    """学习资料库 — 视频/文章/音频"""
    items = [
        # 视频
        {"title": "英语发音入门 - 元音篇", "description": "系统讲解英语 12 个元音的发音方法", "material_type": "video", "url": "/materials/video/vowels_intro.mp4", "cefr_level": "A1", "category": "发音", "duration_seconds": 600, "focus_dimensions": ["speaking"]},
        {"title": "日常对话 100 句", "description": "精选 100 个高频日常对话场景", "material_type": "video", "url": "/materials/video/daily_100.mp4", "cefr_level": "A2", "category": "对话", "duration_seconds": 900, "focus_dimensions": ["speaking", "listening"]},
        {"title": "商务英语面试技巧", "description": "外企面试常见问题与回答策略", "material_type": "video", "url": "/materials/video/biz_interview.mp4", "cefr_level": "B1", "category": "商务", "duration_seconds": 1200, "focus_dimensions": ["speaking", "grammar"]},
        {"title": "TED 演讲：语言学习的秘密", "description": "关于如何高效学习语言的 TED 演讲", "material_type": "video", "url": "/materials/video/ted_language.mp4", "cefr_level": "B2", "category": "学术", "duration_seconds": 1080, "focus_dimensions": ["listening", "speaking"]},
        # 文章
        {"title": "英语音标完全指南", "description": "48 个国际音标的详细发音图解", "material_type": "article", "url": "/materials/article/ipa_guide.html", "cefr_level": "A1", "category": "发音", "focus_dimensions": ["speaking"]},
        {"title": "常见语法错误 Top 20", "description": "中国学生最常犯的 20 个英语语法错误", "material_type": "article", "url": "/materials/article/grammar_top20.html", "cefr_level": "A2", "category": "语法", "focus_dimensions": ["grammar"]},
        {"title": "如何提高英语口语流利度", "description": "5 个实用技巧帮助你说得更流利", "material_type": "article", "url": "/materials/article/fluency_tips.html", "cefr_level": "B1", "category": "口语", "focus_dimensions": ["speaking"]},
        {"title": "学术写作常用连接词", "description": "提升写作逻辑性的 50 个连接词", "material_type": "article", "url": "/materials/article/connectors.html", "cefr_level": "B2", "category": "写作", "focus_dimensions": ["grammar", "reading"]},
        # 音频
        {"title": "慢速英语新闻 - 初级", "description": "VOA 慢速英语精选，适合初级听力训练", "material_type": "audio", "url": "/materials/audio/voa_slow.mp3", "cefr_level": "A2", "category": "听力", "duration_seconds": 300, "focus_dimensions": ["listening"]},
        {"title": "BBC 6 Minute English", "description": "BBC 六分钟英语，中级听力训练", "material_type": "audio", "url": "/materials/audio/bbc_6min.mp3", "cefr_level": "B1", "category": "听力", "duration_seconds": 360, "focus_dimensions": ["listening"]},
        {"title": "英语绕口令挑战", "description": "经典英语绕口令，练习发音清晰度", "material_type": "audio", "url": "/materials/audio/tongue_twisters.mp3", "cefr_level": "B1", "category": "发音", "duration_seconds": 180, "focus_dimensions": ["speaking"]},
        {"title": "TED Talks 精选音频", "description": "高难度学术听力材料", "material_type": "audio", "url": "/materials/audio/ted精选.mp3", "cefr_level": "C1", "category": "学术", "duration_seconds": 900, "focus_dimensions": ["listening", "reading"]},
    ]
    for item in items:
        db.add(LearningMaterial(**item))
    print(f"  ✓ 学习资料库：{len(items)} 条")


def seed_faq_entries(db):
    """FAQ 条目 — 预设 10 个常见问题"""
    items = [
        {"question": "如何开始使用 Lingolab？", "answer": "注册账号后，系统会引导您完成英语水平测评。测评完成后即可使用发音评测、AI 对话等全部学习功能。", "category": "product_use", "sort_order": 1},
        {"question": "发音评测是如何工作的？", "answer": "系统使用 AI 语音识别技术分析您的发音，从音素准确度、重音、连读、语调、节奏五个维度进行评分，并给出具体的改进建议。", "category": "product_use", "sort_order": 2},
        {"question": "AI 对话支持哪些场景？", "answer": "目前支持自我介绍、问路、购物、餐厅点餐四个日常场景，以及面试、服务、导游三个角色扮演场景。我们会持续增加更多场景。", "category": "product_use", "sort_order": 3},
        {"question": "如何提高我的 CEFR 等级？", "answer": "坚持每日练习是关键。系统会根据您的薄弱项推荐针对性练习，建议每天完成 3 个学习任务（约 20-30 分钟），持续 2-3 个月通常可以提升一个等级。", "category": "study_advice", "sort_order": 4},
        {"question": "录音时提示未检测到语音怎么办？", "answer": "请检查麦克风权限是否已开启，确保在安静环境中录音，嘴巴距离麦克风 15-30 厘米。如果问题持续，尝试刷新页面或更换浏览器。", "category": "tech_issue", "sort_order": 5},
        {"question": "支持哪些浏览器？", "answer": "系统支持 Chrome 90+、Edge 90+、Firefox 88+ 浏览器。推荐使用 Chrome 以获得最佳体验。移动端请使用浏览器访问，暂不支持微信内置浏览器。", "category": "tech_issue", "sort_order": 6},
        {"question": "如何查看我的学习进度？", "answer": "点击顶部导航的「学习进度」，可以查看雷达图（五维能力）、趋势折线图（分数变化）和日历热力图（打卡记录）。", "category": "product_use", "sort_order": 7},
        {"question": "积分和勋章有什么用？", "answer": "积分反映您的学习投入度，勋章是对特定成就的认可。完成每日任务、闯关、配音挑战都可以获得积分和勋章。", "category": "product_use", "sort_order": 8},
        {"question": "可以退款吗？", "answer": "Lingolab 基础功能完全免费。如有付费项目需要退款，请发送邮件至 support@lingolab.ai 说明情况，我们会在 3 个工作日内处理。", "category": "refund", "sort_order": 9},
        {"question": "如何联系人工客服？", "answer": "如果智能客服无法解决您的问题，请发送邮件至 support@lingolab.ai，我们的客服团队会在 24 小时内回复。", "category": "general", "sort_order": 10},
    ]
    for item in items:
        db.add(FAQEntry(**item))
    print(f"  ✓ FAQ 条目：{len(items)} 条")


def main():
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing = db.query(PronunciationContent).count()
        if existing > 0:
            print(f"发音内容库已有 {existing} 条数据，跳过种子插入。")
            print("如需重新插入，请先清空相关表。")
            return

        print("开始插入种子数据...")
        seed_pronunciation_content(db)
        seed_dubbing_content(db)
        seed_learning_materials(db)
        seed_faq_entries(db)
        db.commit()
        print("\n全部种子数据插入完成！")
    except Exception as e:
        db.rollback()
        print(f"插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
