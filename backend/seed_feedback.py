"""Seed script — 插入测试反馈数据"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine, Base
from app.models.admin import UserFeedback
from app.models.user import UserProfile

# 确保表存在
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # 获取已有用户
        users = db.query(UserProfile).limit(5).all()
        if not users:
            print("⚠️  没有用户数据，请先创建用户")
            return

        feedbacks = [
            {"user_id": users[0].id, "content": "发音评分有时候不太准确，希望能改进", "feedback_type": "feature", "status": "pending"},
            {"user_id": users[min(1, len(users)-1)].id, "content": "对话场景希望能增加酒店入住", "feedback_type": "scene", "status": "pending"},
            {"user_id": users[min(2, len(users)-1)].id, "content": "录音按钮有时没有反应", "feedback_type": "bug", "status": "resolved", "admin_reply": "已修复，请更新到最新版本", "replied_at": "2026-06-25 10:00:00"},
            {"user_id": users[min(3, len(users)-1)].id, "content": "希望能增加每日学习提醒功能", "feedback_type": "feature", "status": "pending"},
            {"user_id": users[min(4, len(users)-1)].id, "content": "闯关模式的题目太简单了", "feedback_type": "other", "status": "pending"},
        ]

        for fb_data in feedbacks:
            existing = db.query(UserFeedback).filter(UserFeedback.user_id == fb_data["user_id"], UserFeedback.content == fb_data["content"]).first()
            if not existing:
                db.add(UserFeedback(**fb_data))

        db.commit()
        print(f"✅ 已插入 {len(feedbacks)} 条测试反馈")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
