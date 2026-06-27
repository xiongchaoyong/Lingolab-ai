"""游戏化闯关服务 — 每日闯关 / 配音挑战 / 积分 / 勋章"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.gamification import UserScore, UserBadge, DubbingContent, DubbingRecord
from app.models.user import UserProfile
from app.models.profile import UserSkillScore

logger = logging.getLogger(__name__)

# ============================================================
# 积分规则常量
# ============================================================

POINTS_RULES = {
    "daily_task": 10,          # 每日任务完成
    "challenge_level": 20,     # 闯关每关通过
    "challenge_all": 30,       # 闯关全通额外奖励
    "dubbing": 30,             # 配音挑战
    "dubbing_high": 20,        # 配音 ≥85 额外奖励
    "streak_bonus": 20,        # 连续打卡额外（每天）
    "pronunciation_high": 15,  # 发音 ≥85
    "share": 5,                # 分享
}

# ============================================================
# 勋章定义
# ============================================================

BADGE_DEFINITIONS = {
    "newcomer": {
        "name": "新手上路",
        "description": "完成第一次发音练习",
    },
    "streak": {
        "name": "坚持之星",
        "description": "连续打卡 7 天",
    },
    "pronunciation_break": {
        "name": "发音突破",
        "description": "发音评分 ≥85 累计 10 次",
    },
    "progress": {
        "name": "进步达人",
        "description": "CEFR 等级提升一级",
    },
    "dubbing": {
        "name": "配音达人",
        "description": "完成 20 次配音挑战",
    },
    "perfect": {
        "name": "满分挑战",
        "description": "单次发音评分获得满分",
    },
    "scholar": {
        "name": "学霸成就",
        "description": "每日闯关全部通过累计 10 次",
    },
}

# ============================================================
# 每日闯关内容（5 关，难度递增）
# ============================================================

DAILY_CHALLENGE_SENTENCES = [
    {"level": 1, "text": "I'd like a cup of coffee.", "difficulty": "A1", "pass_score": 70},
    {"level": 2, "text": "Could you tell me how to get to the station?", "difficulty": "A2", "pass_score": 70},
    {"level": 3, "text": "The environment is a topic that concerns everyone.", "difficulty": "B1", "pass_score": 70},
    {"level": 4, "text": "The sophisticated technology revolutionized the industry.", "difficulty": "B1", "pass_score": 70},
    {"level": 5, "text": "Nevertheless, the implications of climate change are profound.", "difficulty": "B2", "pass_score": 70},
]

# ============================================================
# 配音内容（硬编码，后续可改为从数据库读取）
# ============================================================

DUBBING_CLIPS = [
    {
        "id": 1, "title": "Toy Story", "source": "Toy Story (1995)",
        "difficulty": "easy", "duration": 5,
        "subtitle": "To infinity and beyond!",
    },
    {
        "id": 2, "title": "Apollo 13", "source": "Apollo 13 (1995)",
        "difficulty": "medium", "duration": 8,
        "subtitle": "Houston, we have a problem.",
    },
    {
        "id": 3, "title": "The King's Speech", "source": "The King's Speech (2010)",
        "difficulty": "medium", "duration": 6,
        "subtitle": "I have a voice!",
    },
    {
        "id": 4, "title": "Braveheart", "source": "Braveheart (1995)",
        "difficulty": "hard", "duration": 12,
        "subtitle": "They may take our lives, but they will never take our freedom!",
    },
]


# ============================================================
# 每日闯关服务
# ============================================================

class DailyChallengeService:
    """每日闯关：5 关递增难度，每关跟读发音评分 ≥70 通过"""

    def get_daily_content(self, user_id: int, db: Session) -> Dict:
        """
        获取今日闯关内容。
        返回 5 关内容 + 用户今日进度。
        """
        today = date.today().isoformat()
        return {
            "levels": DAILY_CHALLENGE_SENTENCES,
            "date": today,
            "completed": False,
            "current_level": 1,
            "level_scores": {},
        }

    async def assess_level(
        self, audio_path: str, text: str, mode: str = "sentence"
    ) -> Dict:
        """
        对单关录音进行发音评分。
        复用 PronunciationService.score()。
        """
        from app.services.pronunciation import score_audio

        result = await score_audio(audio_path, text, mode)
        dimensions_list = result.get("dimensions", [])
        return {
            "overall": result.get("overall", 0),
            "dimensions": {d["label"]: d["score"] for d in dimensions_list},
            "dimensions_list": dimensions_list,  # 供 ingest_pronunciation_scores 使用
        }

    def award_daily_points(
        self, user_id: int, levels_passed: int, all_completed: bool, db: Session
    ) -> Tuple[int, List[str]]:
        """
        计算并发放闯关积分。
        返回 (本次积分, 新勋章类型列表)。
        """
        points_earned = levels_passed * POINTS_RULES["challenge_level"]
        if all_completed:
            points_earned += POINTS_RULES["challenge_all"]

        # 写入积分记录
        desc = f"每日闯关通过 {levels_passed}/5 关"
        if all_completed:
            desc += "（全通奖励）"
        PointsService.add_points(user_id, "challenge", points_earned, desc, db)

        # 检查勋章
        new_badges = BadgeService.check_and_award(user_id, "daily_complete", db)

        return points_earned, new_badges


# ============================================================
# 配音挑战服务
# ============================================================

class DubbingService:
    """配音挑战：影视片段配音，三维评分（发音50%+语调30%+情感20%）"""

    def get_content_list(self, difficulty: Optional[str] = None) -> List[Dict]:
        """获取配音内容列表"""
        clips = DUBBING_CLIPS
        if difficulty:
            clips = [c for c in clips if c["difficulty"] == difficulty]
        return clips

    async def score_dubbing(
        self, audio_path: str, content_id: int, user_id: int, db: Session
    ) -> Dict:
        """
        对配音录音进行三维评分。
        发音维度：调用 PronunciationService
        语调维度：基于音频能量分析（简化）
        情感维度：基于 LLM 分析（简化，无 LLM 时用默认值）
        """
        # 找到对应内容
        clip = next((c for c in DUBBING_CLIPS if c["id"] == content_id), None)
        if not clip:
            raise ValueError(f"配音内容 {content_id} 不存在")

        from app.services.pronunciation import score_audio

        # 发音评分（权重 50%）
        pron_result = await score_audio(audio_path, clip["subtitle"], "sentence")
        pronunciation_score = pron_result.get("overall", 60)

        # 语调评分（权重 30%）— 简化：基于音频 RMS 能量分析
        intonation_score = self._analyze_intonation_simple(audio_path)

        # 情感评分（权重 20%）— 简化：默认中等分
        emotion_score = self._analyze_emotion_simple(audio_path)

        # 综合评分
        total_score = round(
            pronunciation_score * 0.5 + intonation_score * 0.3 + emotion_score * 0.2, 1
        )

        # 写入配音记录
        record = DubbingRecord(
            user_id=user_id,
            content_id=content_id,
            audio_url=audio_path,
            pronunciation_score=round(pronunciation_score, 2),
            intonation_score=round(intonation_score, 2),
            emotion_score=round(emotion_score, 2),
            total_score=total_score,
        )
        db.add(record)
        db.flush()

        # 发放积分
        points = POINTS_RULES["dubbing"]
        if total_score >= 85:
            points += POINTS_RULES["dubbing_high"]
        PointsService.add_points(user_id, "dubbing", points, f"配音《{clip['title']}》", db)

        # 检查勋章
        new_badges = BadgeService.check_and_award(user_id, "dubbing_complete", db)

        return {
            "content_id": content_id,
            "pronunciation_score": round(pronunciation_score, 1),
            "intonation_score": round(intonation_score, 1),
            "emotion_score": round(emotion_score, 1),
            "total_score": total_score,
            "points_earned": points,
            "new_badges": [
                {"badge_type": b, "badge_name": BADGE_DEFINITIONS[b]["name"]}
                for b in new_badges
            ],
        }

    def _analyze_intonation_simple(self, audio_path: str) -> float:
        """简化的语调分析：基于音频 RMS 能量变化"""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            rms = librosa.feature.rms(y=y)[0]
            if len(rms) < 2:
                return 60.0
            # 能量变异系数 → 语调丰富度
            cv = float(rms.std() / (rms.mean() + 1e-8))
            score = min(95, max(30, 50 + cv * 40))
            return round(score, 1)
        except Exception:
            return 60.0

    def _analyze_emotion_simple(self, audio_path: str) -> float:
        """简化的情感分析：基于音高变化"""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            # 提取基频
            f0, _, _ = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
            valid_f0 = f0[~np.isnan(f0)]
            if len(valid_f0) < 2:
                return 60.0
            import numpy as np
            # 音高变化 → 情感表达力
            f0_range = float(valid_f0.max() - valid_f0.min())
            f0_std = float(valid_f0.std())
            score = min(95, max(30, 40 + f0_range * 0.4 + f0_std * 0.6))
            return round(score, 1)
        except Exception:
            return 60.0

    def get_user_records(
        self, user_id: int, db: Session, limit: int = 20
    ) -> List[Dict]:
        """获取用户配音历史"""
        records = (
            db.query(DubbingRecord)
            .filter(DubbingRecord.user_id == user_id)
            .order_by(DubbingRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "content_title": next(
                    (c["title"] for c in DUBBING_CLIPS if c["id"] == r.content_id),
                    "未知",
                ),
                "total_score": float(r.total_score) if r.total_score else None,
                "created_at": r.created_at,
            }
            for r in records
        ]


# ============================================================
# 积分服务
# ============================================================

class PointsService:
    """积分管理：加减积分、查询历史、排行榜"""

    @staticmethod
    def add_points(
        user_id: int,
        action_type: str,
        score: int,
        description: str = "",
        db: Session = None,
    ) -> UserScore:
        """添加积分记录"""
        record = UserScore(
            user_id=user_id,
            action_type=action_type,
            score=score,
            description=description,
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def get_total_points(user_id: int, db: Session) -> int:
        """获取用户总积分"""
        result = (
            db.query(func.sum(UserScore.score))
            .filter(UserScore.user_id == user_id)
            .scalar()
        )
        return result or 0

    @staticmethod
    def get_recent_records(
        user_id: int, db: Session, limit: int = 20
    ) -> List[Dict]:
        """获取最近积分记录"""
        records = (
            db.query(UserScore)
            .filter(UserScore.user_id == user_id)
            .order_by(UserScore.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "action_type": r.action_type,
                "score": r.score,
                "description": r.description,
                "created_at": r.created_at,
            }
            for r in records
        ]

    @staticmethod
    def get_leaderboard(db: Session, limit: int = 20) -> List[Dict]:
        """获取积分排行榜"""
        rows = (
            db.query(
                UserScore.user_id,
                UserProfile.username,
                func.sum(UserScore.score).label("total_points"),
            )
            .join(UserProfile, UserScore.user_id == UserProfile.id)
            .group_by(UserScore.user_id, UserProfile.username)
            .order_by(text("total_points DESC"))
            .limit(limit)
            .all()
        )

        result = []
        for rank, row in enumerate(rows, 1):
            badge_count = (
                db.query(func.count(UserBadge.id))
                .filter(UserBadge.user_id == row.user_id)
                .scalar()
            )
            result.append({
                "rank": rank,
                "user_id": row.user_id,
                "username": row.username,
                "total_points": int(row.total_points),
                "badge_count": badge_count or 0,
            })
        return result


# ============================================================
# 勋章服务
# ============================================================

class BadgeService:
    """勋章管理：7 种勋章检测与发放"""

    @staticmethod
    def check_and_award(
        user_id: int, trigger_event: str, db: Session
    ) -> List[str]:
        """
        根据触发事件检查并发放勋章。
        返回新获得的勋章类型列表。
        """
        existing = BadgeService._get_existing_badge_types(user_id, db)
        new_badges = []

        # 新手上路：完成第一次发音练习
        if trigger_event in ("pronunciation_complete", "daily_complete", "dubbing_complete"):
            if "newcomer" not in existing:
                # 检查是否有任何发音相关记录
                score_count = (
                    db.query(func.count(UserSkillScore.id))
                    .filter(UserSkillScore.user_id == user_id)
                    .scalar()
                )
                if score_count and score_count >= 1:
                    BadgeService._award(user_id, "newcomer", db)
                    new_badges.append("newcomer")
                    existing.add("newcomer")

        # 坚持之星：连续打卡 7 天
        if trigger_event in ("daily_complete", "login"):
            if "streak" not in existing:
                streak = BadgeService._calc_streak(user_id, db)
                if streak >= 7:
                    BadgeService._award(user_id, "streak", db)
                    new_badges.append("streak")
                    existing.add("streak")

        # 发音突破：发音 ≥85 累计 10 次
        if trigger_event in ("pronunciation_complete", "daily_complete", "dubbing_complete"):
            if "pronunciation_break" not in existing:
                high_count = (
                    db.query(func.count(UserSkillScore.id))
                    .filter(
                        UserSkillScore.user_id == user_id,
                        UserSkillScore.score >= 85,
                    )
                    .scalar()
                )
                if high_count and high_count >= 10:
                    BadgeService._award(user_id, "pronunciation_break", db)
                    new_badges.append("pronunciation_break")
                    existing.add("pronunciation_break")

        # 进步达人：CEFR 等级提升
        if trigger_event == "level_up":
            if "progress" not in existing:
                BadgeService._award(user_id, "progress", db)
                new_badges.append("progress")
                existing.add("progress")

        # 配音达人：完成 20 次配音
        if trigger_event == "dubbing_complete":
            if "dubbing" not in existing:
                dub_count = (
                    db.query(func.count(DubbingRecord.id))
                    .filter(DubbingRecord.user_id == user_id)
                    .scalar()
                )
                if dub_count and dub_count >= 20:
                    BadgeService._award(user_id, "dubbing", db)
                    new_badges.append("dubbing")
                    existing.add("dubbing")

        # 满分挑战：单次发音满分
        if trigger_event in ("pronunciation_complete", "daily_complete"):
            if "perfect" not in existing:
                perfect_count = (
                    db.query(func.count(UserSkillScore.id))
                    .filter(
                        UserSkillScore.user_id == user_id,
                        UserSkillScore.score == 100,
                    )
                    .scalar()
                )
                if perfect_count and perfect_count >= 1:
                    BadgeService._award(user_id, "perfect", db)
                    new_badges.append("perfect")
                    existing.add("perfect")

        # 学霸成就：全通闯关 10 次
        if trigger_event == "daily_complete":
            if "scholar" not in existing:
                # 检查 user_scores 中 challenge 全通次数
                all_pass_count = (
                    db.query(func.count(UserScore.id))
                    .filter(
                        UserScore.user_id == user_id,
                        UserScore.action_type == "challenge",
                        UserScore.score >= 130,  # 100(20*5) + 30 全通
                    )
                    .scalar()
                )
                if all_pass_count and all_pass_count >= 10:
                    BadgeService._award(user_id, "scholar", db)
                    new_badges.append("scholar")
                    existing.add("scholar")

        return new_badges

    @staticmethod
    def get_user_badges(user_id: int, db: Session) -> List[Dict]:
        """获取用户勋章列表（含未获得的定义）"""
        earned = BadgeService._get_existing_badge_types(user_id, db)
        earned_details = {
            b.badge_type: b.awarded_at
            for b in db.query(UserBadge)
            .filter(UserBadge.user_id == user_id)
            .all()
        }

        result = []
        for badge_type, info in BADGE_DEFINITIONS.items():
            result.append({
                "badge_type": badge_type,
                "badge_name": info["name"],
                "description": info["description"],
                "earned": badge_type in earned,
                "awarded_at": earned_details.get(badge_type),
            })
        return result

    @staticmethod
    def _award(user_id: int, badge_type: str, db: Session):
        """发放勋章（利用 UNIQUE 约束防重复）"""
        try:
            badge = UserBadge(
                user_id=user_id,
                badge_type=badge_type,
                badge_name=BADGE_DEFINITIONS[badge_type]["name"],
            )
            db.add(badge)
            db.flush()
            logger.info(f"用户 {user_id} 获得勋章: {BADGE_DEFINITIONS[badge_type]['name']}")
        except Exception as e:
            logger.warning(f"勋章发放失败（可能已存在）: {e}")

    @staticmethod
    def _get_existing_badge_types(user_id: int, db: Session) -> set:
        """获取用户已拥有的勋章类型集合"""
        badges = (
            db.query(UserBadge.badge_type)
            .filter(UserBadge.user_id == user_id)
            .all()
        )
        return {b[0] for b in badges}

    @staticmethod
    def _calc_streak(user_id: int, db: Session) -> int:
        """计算用户连续打卡天数"""
        # 从 user_scores 获取所有有活动的日期
        rows = (
            db.query(func.date(UserScore.created_at).label("activity_date"))
            .filter(UserScore.user_id == user_id)
            .group_by(text("activity_date"))
            .order_by(text("activity_date DESC"))
            .all()
        )

        if not rows:
            return 0

        dates = [r[0] for r in rows]
        today = date.today()

        # 只有今天或昨天有活动才算连续
        if dates[0] < today - timedelta(days=1):
            return 0

        streak = 1
        for i in range(1, len(dates)):
            if (dates[i - 1] - dates[i]).days == 1:
                streak += 1
            else:
                break

        return streak


# 单例
challenge_service = DailyChallengeService()
dubbing_service = DubbingService()