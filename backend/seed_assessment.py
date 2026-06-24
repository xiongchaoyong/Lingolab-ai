"""种子数据 — 将自适应测评题目写入 assessment_questions 表（30 题，覆盖 A2/B1/B2）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.assessment import AssessmentQuestion
from sqlalchemy import text

# 30 题：听力8 + 口语6 + 阅读8 + 语法8
# A2:9, B1:11, B2:10
QUESTIONS = [
    # ========== 听力 (8题: A2×2, B1×3, B2×3) ==========
    {
        "question_text": "听力：What does the woman mean? (Audio clip about weekend plans)",
        "options": ["A. She likes to travel", "B. She works at a hospital", "C. She is studying medicine", "D. She wants to be a teacher"],
        "correct_option": 1, "dimension": "listening", "difficulty": "B1",
    },
    {
        "question_text": "听力：Where does this conversation probably take place? (Audio clip about ordering food)",
        "options": ["A. In a library", "B. In a restaurant", "C. In a hospital", "D. In a classroom"],
        "correct_option": 2, "dimension": "listening", "difficulty": "A2",
    },
    {
        "question_text": "听力：What is the speaker's attitude toward the proposal? (Audio clip about a business plan)",
        "options": ["A. Enthusiastic", "B. Skeptical", "C. Neutral", "D. Confused"],
        "correct_option": 2, "dimension": "listening", "difficulty": "B2",
    },
    {
        "question_text": "听力：What time will the meeting start? (Audio clip about a schedule change)",
        "options": ["A. 9:00 AM", "B. 10:00 AM", "C. 11:00 AM", "D. 2:00 PM"],
        "correct_option": 2, "dimension": "listening", "difficulty": "A2",
    },
    {
        "question_text": "听力：What is the main topic of the lecture? (Audio clip about renewable energy)",
        "options": ["A. Fossil fuels", "B. Solar power technology", "C. Nuclear energy safety", "D. Wind farm construction"],
        "correct_option": 2, "dimension": "listening", "difficulty": "B1",
    },
    {
        "question_text": "听力：Why did the man miss his flight? (Audio clip about travel delays)",
        "options": ["A. Traffic jam", "B. Lost passport", "C. Weather cancellation", "D. Late check-in"],
        "correct_option": 1, "dimension": "listening", "difficulty": "B1",
    },
    {
        "question_text": "听力：What conclusion does the speaker reach? (Audio clip about economic trends)",
        "options": ["A. The market will recover quickly", "B. Long-term investment is safer", "C. Short-term gains are guaranteed", "D. All investments carry equal risk"],
        "correct_option": 2, "dimension": "listening", "difficulty": "B2",
    },
    {
        "question_text": "听力：What does the professor suggest students do? (Audio clip about academic research)",
        "options": ["A. Submit papers early", "B. Use primary sources", "C. Avoid controversial topics", "D. Work in groups only"],
        "correct_option": 2, "dimension": "listening", "difficulty": "B2",
    },

    # ========== 口语 (6题: A2×2, B1×2, B2×2) ==========
    {
        "question_text": "Speaking: Describe your favorite food. What is it? Why do you like it? How often do you eat it?",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "B1",
    },
    {
        "question_text": "Speaking: Talk about a memorable trip you have taken. Where did you go? Who did you go with? What made it special?",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "B2",
    },
    {
        "question_text": "Speaking: Describe your daily routine. What do you usually do in the morning, afternoon, and evening?",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "A2",
    },
    {
        "question_text": "Speaking: Describe your best friend. What does he/she look like? What do you like to do together?",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "A2",
    },
    {
        "question_text": "Speaking: What are the advantages and disadvantages of working from home? Give specific examples.",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "B1",
    },
    {
        "question_text": "Speaking: Should governments invest more in space exploration or ocean research? Explain your reasoning with examples.",
        "options": [], "correct_option": 0, "dimension": "speaking", "difficulty": "B2",
    },

    # ========== 阅读 (8题: A2×2, B1×3, B2×3) ==========
    {
        "question_text": "Reading: Choose the best word to fill in the blank.\n\n\"The company has _____ its profits by 20% this year.\"",
        "options": ["A. increased", "B. decreased", "C. maintained", "D. predicted"],
        "correct_option": 1, "dimension": "reading", "difficulty": "B1",
    },
    {
        "question_text": "Reading: What is the main idea of the passage?\n\n\"Climate change has become one of the most pressing issues of our time. Scientists warn that rising temperatures could lead to severe consequences including extreme weather events, sea level rise, and biodiversity loss.\"",
        "options": ["A. Weather is unpredictable", "B. Climate change poses serious threats", "C. Scientists disagree on climate issues", "D. Biodiversity is decreasing naturally"],
        "correct_option": 2, "dimension": "reading", "difficulty": "B2",
    },
    {
        "question_text": "Reading: According to the text, which statement is TRUE?\n\n\"Regular exercise has been shown to improve both physical and mental health. Studies indicate that even 30 minutes of moderate activity per day can reduce the risk of heart disease by up to 30%.\"",
        "options": ["A. Exercise only benefits physical health", "B. 30 minutes of daily exercise can lower heart disease risk", "C. Mental health is unrelated to exercise", "D. Only intense exercise provides health benefits"],
        "correct_option": 2, "dimension": "reading", "difficulty": "B1",
    },
    {
        "question_text": "Reading: What does the notice say?\n\n\"Library Notice: Books may be borrowed for up to two weeks. Late returns will be charged $0.50 per day. Reference books cannot be taken out of the library.\"",
        "options": ["A. All books can be borrowed for one week", "B. Reference books must stay in the library", "C. Late fees are $1.00 per day", "D. Books can be borrowed for one month"],
        "correct_option": 2, "dimension": "reading", "difficulty": "A2",
    },
    {
        "question_text": "Reading: What is the author's purpose?\n\n\"Many people believe that success comes from talent alone. However, research shows that deliberate practice and persistence are far more important factors. The most successful individuals are not necessarily the most gifted, but those who work hardest.\"",
        "options": ["A. To argue that talent is most important", "B. To show that hard work matters more than talent", "C. To describe different types of success", "D. To compare successful people"],
        "correct_option": 2, "dimension": "reading", "difficulty": "B1",
    },
    {
        "question_text": "Reading: Choose the best title for the article.\n\n\"Artificial intelligence is transforming industries from healthcare to transportation. While AI promises increased efficiency and new capabilities, experts warn that ethical considerations must be addressed, including privacy concerns, job displacement, and algorithmic bias.\"",
        "options": ["A. The History of Computers", "B. AI: Promise and Peril", "C. How to Build a Robot", "D. Jobs of the Future"],
        "correct_option": 2, "dimension": "reading", "difficulty": "B2",
    },
    {
        "question_text": "Reading: What can be inferred from the text?\n\n\"Tom checked his watch for the third time in ten minutes. The train was already twenty minutes late, and he had a job interview in an hour. He pulled out his phone and started looking for alternative routes.\"",
        "options": ["A. Tom enjoys waiting for trains", "B. Tom is worried about being late for his interview", "C. Tom has rescheduled his interview", "D. Tom decided to cancel his trip"],
        "correct_option": 2, "dimension": "reading", "difficulty": "A2",
    },
    {
        "question_text": "Reading: What does the underlined word refer to?\n\n\"The Industrial Revolution brought unprecedented changes to society. It not only transformed manufacturing but also reshaped social structures, urban development, and global trade patterns.\"",
        "options": ["A. Society", "B. Manufacturing", "C. The Industrial Revolution", "D. Global trade"],
        "correct_option": 3, "dimension": "reading", "difficulty": "B2",
    },

    # ========== 语法 (8题: A2×3, B1×3, B2×2) ==========
    {
        "question_text": "Grammar: Choose the correct sentence.",
        "options": ["A. She don't like coffee", "B. She doesn't likes coffee", "C. She doesn't like coffee", "D. She not like coffee"],
        "correct_option": 3, "dimension": "grammar", "difficulty": "A2",
    },
    {
        "question_text": "Grammar: \"If I _____ rich, I would travel around the world.\"",
        "options": ["A. am", "B. was", "C. were", "D. be"],
        "correct_option": 3, "dimension": "grammar", "difficulty": "B1",
    },
    {
        "question_text": "Grammar: \"He _____ to the gym every day after work.\"",
        "options": ["A. go", "B. goes", "C. going", "D. gone"],
        "correct_option": 2, "dimension": "grammar", "difficulty": "A2",
    },
    {
        "question_text": "Grammar: \"They have been living here _____ 2015.\"",
        "options": ["A. for", "B. since", "C. from", "D. in"],
        "correct_option": 2, "dimension": "grammar", "difficulty": "A2",
    },
    {
        "question_text": "Grammar: \"By the time we arrived, the movie _____ .\"",
        "options": ["A. already started", "B. has already started", "C. had already started", "D. was already started"],
        "correct_option": 3, "dimension": "grammar", "difficulty": "B1",
    },
    {
        "question_text": "Grammar: \"The report, along with the supporting documents, _____ submitted yesterday.\"",
        "options": ["A. were", "B. was", "C. are", "D. have been"],
        "correct_option": 2, "dimension": "grammar", "difficulty": "B1",
    },
    {
        "question_text": "Grammar: \"Not until the teacher entered the classroom _____ talking.\"",
        "options": ["A. the students stopped", "B. did the students stop", "C. the students did stop", "D. stopped the students"],
        "correct_option": 2, "dimension": "grammar", "difficulty": "B2",
    },
    {
        "question_text": "Grammar: \"It is essential that every student _____ the safety guidelines before the lab session.\"",
        "options": ["A. reads", "B. read", "C. reading", "D. has read"],
        "correct_option": 2, "dimension": "grammar", "difficulty": "B2",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(AssessmentQuestion).count()
        if existing >= 30:
            print(f"题库已有 {existing} 道题，跳过种子数据")
            return

        # 清空重插
        db.execute(text("DELETE FROM assessment_questions"))
        db.commit()

        for q in QUESTIONS:
            record = AssessmentQuestion(**q)
            db.add(record)

        db.commit()
        print(f"成功插入 {len(QUESTIONS)} 道题目")
    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()