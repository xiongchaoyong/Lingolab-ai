"""ProfileUpdater — EMA 驱动的用户画像动态更新服务

流程：
1. 练习完成后调用 ingest_*() 写入 UserSkillScore
2. 自动调用 recalculate() 用 EMA 重算各维度分数
3. 更新 user_profiles.level_final
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import UserProfile
from app.models.profile import UserSkillScore, DimensionScoreLog
from app.models.knowledge_graph import DailyTask

logger = logging.getLogger(__name__)

# CEFR 定级阈值（与 assessment.py 保持一致）
CEFR_THRESHOLDS = [
    (96, "C2"),
    (81, "C1"),
    (61, "B2"),
    (41, "B1"),
    (21, "A2"),
    (0, "A1"),
]

# EMA 参数
EMA_ALPHA = 0.3  # 新分数权重
MAX_DAYS = 30     # 只计算最近 30 天

# 发音维度 → 用户画像维度映射
PRONUNCIATION_DIM_MAP = {
    "phoneme_accuracy": "speaking",
    "stress": "speaking",
    "intonation": "speaking",
    "linking": "speaking",
    "rhythm": "speaking",
}

# 对话文本维度 → 用户画像维度映射
TEXT_DIM_MAP = {
    "语法正确率": "grammar",
    "词汇丰富度": "reading",
    "对话参与度": "speaking",
}

# 任务类型 → 用户画像维度映射
TASK_DIM_MAP = {
    "shadowing": "speaking",
    "conversation": "speaking",
    "listening": "listening",
}


def _get_cefr(score: float) -> str:
    """根据分数返回 CEFR 等级"""
    for threshold, level in CEFR_THRESHOLDS:
        if score >= threshold:
            return level
    return "A1"


class ProfileUpdater:
    """用户画像动态更新器"""

    # ============================================================
    # 分数摄入
    # ============================================================

    def ingest_pronunciation_scores(
        self, user_id: int, dimensions: List[dict], source_id: int, db: Session,
    ):
        """摄入发音评测分数

        Args:
            dimensions: [{label: '音素准确度', score: 85}, ...]
        """
        label_map = {
            "音素准确度": "phoneme_accuracy",
            "重音位置": "stress",
            "语调曲线": "intonation",
            "连读表现": "linking",
            "节奏感": "rhythm",
        }

        for dim in dimensions:
            eng_name = label_map.get(dim["label"], dim["label"])
            mapped_dim = PRONUNCIATION_DIM_MAP.get(eng_name, "speaking")

            db.add(UserSkillScore(
                user_id=user_id,
                dimension=mapped_dim,
                skill_name=f"pronunciation:{eng_name}",
                score=dim["score"],
                source="pronunciation",
                source_id=source_id,
            ))

        self.recalculate(user_id, db, source="pronunciation", source_id=source_id)

    def ingest_conversation_scores(
        self, user_id: int, pronunciation: List[dict],
        text_dimensions: List[dict], source_id: int, db: Session,
    ):
        """摄入对话评分

        Args:
            pronunciation: [{label: '音素准确度', score: 80}, ...] (5 个语音维度)
            text_dimensions: [{label: '语法正确率', score: 75}, ...] (3 个文本维度)
        """
        # 语音维度
        for dim in pronunciation:
            db.add(UserSkillScore(
                user_id=user_id,
                dimension="speaking",
                skill_name=f"conversation:pronunciation:{dim['label']}",
                score=dim["score"],
                source="conversation",
                source_id=source_id,
            ))

        # 文本维度
        for dim in text_dimensions:
            mapped_dim = TEXT_DIM_MAP.get(dim["label"], "speaking")
            db.add(UserSkillScore(
                user_id=user_id,
                dimension=mapped_dim,
                skill_name=f"conversation:text:{dim['label']}",
                score=dim["score"],
                source="conversation",
                source_id=source_id,
            ))

        self.recalculate(user_id, db, source="conversation", source_id=source_id)

    def ingest_task_score(self, user_id: int, task: DailyTask, db: Session):
        """摄入任务完成分数"""
        dimension = TASK_DIM_MAP.get(task.task_type, "speaking")
        score = float(task.score) if task.score else 70.0

        db.add(UserSkillScore(
            user_id=user_id,
            dimension=dimension,
            skill_name=f"task:{task.task_type}",
            score=score,
            source="daily_task",
            source_id=task.id,
        ))

        self.recalculate(user_id, db, source="daily_task", source_id=task.id)

    def ingest_assessment_scores(
        self, user_id: int, dimension_scores: Dict[str, float],
        session_id: str, db: Session,
    ):
        """摄入测评结果 — 初次测评完成后调用

        Args:
            dimension_scores: {listening: 72.5, speaking: 68.3, reading: 80.0, grammar: 55.0}
            session_id: 测评会话 UUID
        """
        for dim, score in dimension_scores.items():
            db.add(UserSkillScore(
                user_id=user_id,
                dimension=dim,
                skill_name=f"assessment:{dim}",
                score=score,
                source="assessment",
                source_id=None,  # session 是 UUID，存不进 Integer，用 None
            ))

        # 先 flush 让 UserSkillScore 落库，再 recalculate 就能读到
        db.flush()
        self.recalculate(user_id, db, source="assessment", source_id=None)

    # ============================================================
    # EMA 计算
    # ============================================================

    def get_dimension_averages(self, user_id: int, db: Session) -> Dict[str, Optional[float]]:
        """计算各维度 EMA 分数"""
        cutoff = datetime.utcnow() - timedelta(days=MAX_DAYS)

        scores = (
            db.query(UserSkillScore)
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= cutoff,
            )
            .order_by(UserSkillScore.created_at.asc())
            .all()
        )

        # 按维度分组
        dimension_values = {
            "listening": [],
            "speaking": [],
            "reading": [],
            "grammar": [],
        }
        for s in scores:
            if s.dimension in dimension_values:
                dimension_values[s.dimension].append(float(s.score))

        # EMA 计算
        result = {}
        for dim, vals in dimension_values.items():
            if not vals:
                result[dim] = None
                continue
            ema = vals[0]
            for v in vals[1:]:
                ema = v * EMA_ALPHA + ema * (1 - EMA_ALPHA)
            result[dim] = round(ema, 1)

        return result

    def get_recent_scores(self, user_id: int, db: Session, limit: int = 100) -> List[dict]:
        """获取最近分数记录"""
        scores = (
            db.query(UserSkillScore)
            .filter(UserSkillScore.user_id == user_id)
            .order_by(UserSkillScore.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "dimension": s.dimension,
                "skill_name": s.skill_name,
                "score": float(s.score),
                "source": s.source,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in scores
        ]

    # ============================================================
    # 画像重算
    # ============================================================

    def recalculate(
        self, user_id: int, db: Session,
        source: str = "manual_refresh", source_id: int = None,
    ) -> Tuple[Optional[str], Dict[str, Optional[float]]]:
        """重算 level_final 并更新数据库"""
        dim_avgs = self.get_dimension_averages(user_id, db)

        # 只考虑有值的维度
        valid_dims = {k: v for k, v in dim_avgs.items() if v is not None}
        overall = None
        new_level = None
        if valid_dims:
            # 综合分 = 有效维度均分
            overall = sum(valid_dims.values()) / len(valid_dims)
            new_level = _get_cefr(overall)

            # 更新 user_profiles
            user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
            if user:
                old_level = user.level_final
                user.level_final = new_level
                logger.info(
                    f"用户 {user_id} ({user.username}) 画像更新: "
                    f"level {old_level} → {new_level}, overall={overall:.1f}"
                )

        # 记录维度分数变更日志
        self._log_scores(user_id, dim_avgs, overall, new_level, source, source_id, db)

        return new_level, dim_avgs

    # ============================================================
    # 分数变更日志
    # ============================================================

    def _log_scores(
        self, user_id: int, dim_avgs: Dict[str, Optional[float]],
        overall: Optional[float], cefr: Optional[str],
        source: str, source_id: Optional[int], db: Session,
    ):
        """写入维度分数变更日志"""
        db.add(DimensionScoreLog(
            user_id=user_id,
            source=source,
            source_id=source_id,
            listening_score=dim_avgs.get("listening"),
            speaking_score=dim_avgs.get("speaking"),
            reading_score=dim_avgs.get("reading"),
            grammar_score=dim_avgs.get("grammar"),
            overall_score=round(overall, 1) if overall is not None else None,
            cefr_level=cefr,
        ))

    def get_score_logs(self, user_id: int, db: Session, limit: int = 20) -> List[dict]:
        """获取维度分数变更日志"""
        logs = (
            db.query(DimensionScoreLog)
            .filter(DimensionScoreLog.user_id == user_id)
            .order_by(DimensionScoreLog.created_at.desc())
            .limit(limit)
            .all()
        )

        SOURCE_LABELS = {
            "assessment": "初次测评",
            "pronunciation": "发音评测",
            "conversation": "智能对话",
            "roleplay": "情景角色扮演",
            "daily_task": "每日任务",
            "manual_refresh": "手动刷新",
        }

        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "source": log.source,
                "source_label": SOURCE_LABELS.get(log.source, log.source),
                "listening_score": float(log.listening_score) if log.listening_score is not None else None,
                "speaking_score": float(log.speaking_score) if log.speaking_score is not None else None,
                "reading_score": float(log.reading_score) if log.reading_score is not None else None,
                "grammar_score": float(log.grammar_score) if log.grammar_score is not None else None,
                "overall_score": float(log.overall_score) if log.overall_score is not None else None,
                "cefr_level": log.cefr_level,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            })
        return result


# 全局单例
profile_updater = ProfileUpdater()