"""种子数据 — 将前端 Mock 题目写入 assessment_questions 表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.assessment import AssessmentQuestion
from sqlalchemy import text

QUESTIONS = [
    {
        "question_text": "听力：What does the woman mean? (Audio clip about weekend plans)",
        "options": ["A. She likes to travel", "B. She works at a hospital", "C. She is studying medicine", "D. She wants to be a teacher"],
        "correct_option": 1,
        "dimension": "listening",
        "difficulty": "B1",
    },
    {
        "question_text": 'Reading: Choose the best word to fill in the blank.\n\n"The company has _____ its profits by 20% this year."',
        "options": ["A. increased", "B. decreased", "C. maintained", "D. predicted"],
        "correct_option": 1,
        "dimension": "reading",
        "difficulty": "B1",
    },
    {
        "question_text": "Speaking: Describe your favorite food. What is it? Why do you like it? How often do you eat it?",
        "options": [],
        "correct_option": 0,
        "dimension": "speaking",
        "difficulty": "B1",
    },
    {
        "question_text": "Grammar: Choose the correct sentence.",
        "options": ["A. She don't like coffee", "B. She doesn't likes coffee", "C. She doesn't like coffee", "D. She not like coffee"],
        "correct_option": 3,
        "dimension": "grammar",
        "difficulty": "A2",
    },
    {
        "question_text": "听力：Where does this conversation probably take place? (Audio clip about ordering food)",
        "options": ["A. In a library", "B. In a restaurant", "C. In a hospital", "D. In a classroom"],
        "correct_option": 2,
        "dimension": "listening",
        "difficulty": "A2",
    },
    {
        "question_text": 'Reading: What is the main idea of the passage?\n\n"Climate change has become one of the most pressing issues of our time. Scientists warn that rising temperatures could lead to severe consequences including extreme weather events, sea level rise, and biodiversity loss."',
        "options": ["A. Weather is unpredictable", "B. Climate change poses serious threats", "C. Scientists disagree on climate issues", "D. Biodiversity is decreasing naturally"],
        "correct_option": 2,
        "dimension": "reading",
        "difficulty": "B2",
    },
    {
        "question_text": "Speaking: Talk about a memorable trip you have taken. Where did you go? Who did you go with? What made it special?",
        "options": [],
        "correct_option": 0,
        "dimension": "speaking",
        "difficulty": "B2",
    },
    {
        "question_text": 'Grammar: "If I _____ rich, I would travel around the world."',
        "options": ["A. am", "B. was", "C. were", "D. be"],
        "correct_option": 3,
        "dimension": "grammar",
        "difficulty": "B1",
    },
    {
        "question_text": "听力：What is the speaker's attitude toward the proposal? (Audio clip about a business plan)",
        "options": ["A. Enthusiastic", "B. Skeptical", "C. Neutral", "D. Confused"],
        "correct_option": 2,
        "dimension": "listening",
        "difficulty": "B2",
    },
    {
        "question_text": "Reading: According to the text, which statement is TRUE?\n\n\"Regular exercise has been shown to improve both physical and mental health. Studies indicate that even 30 minutes of moderate activity per day can reduce the risk of heart disease by up to 30%.\"",
        "options": ["A. Exercise only benefits physical health", "B. 30 minutes of daily exercise can lower heart disease risk", "C. Mental health is unrelated to exercise", "D. Only intense exercise provides health benefits"],
        "correct_option": 2,
        "dimension": "reading",
        "difficulty": "B1",
    },
]


def seed():
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(AssessmentQuestion).count()
        if existing >= 10:
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