"""学习预测与预警服务 — 线性回归预测 / 规则预警 / 通知管理"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from math import ceil

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.gamification import Notice, LearningPrediction
from app.models.profile import UserSkillScore

logger = logging.getLogger(__name__)


class PredictionService:
    """学习预测与预警服务"""

    def calculate_prediction(self, user_id: int, db: Session) -> Dict:
        """计算学习预测（线性回归）"""
        # 获取最近30天每日综合分
        daily_scores = self._get_daily_composite_scores(user_id, 30, db)

        if len(daily_scores) < 3:
            return {
                "current_score": daily_scores[-1][1] if daily_scores else 0,
                "trend_slope": None,
                "target_score": 85,
                "predicted_days": None,
                "predicted_date": None,
                "trend": "stable",
                "message": "数据不足，继续学习 3 天后再查看预测",
            }

        # 线性回归 y = slope * x + intercept
        n = len(daily_scores)
        x_sum = sum(i for i, _ in enumerate(daily_scores))
        y_sum = sum(score for _, score in daily_scores)
        xy_sum = sum(i * score for i, (_, score) in enumerate(daily_scores))
        x2_sum = sum(i * i for i in range(n))

        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            slope = 0.0
        else:
            slope = (n * xy_sum - x_sum * y_sum) / denominator

        current_score = daily_scores[-1][1]

        # 读取或默认目标分数
        target_score = self._get_target_score(user_id, db)

        # 趋势方向
        if slope > 0.05:
            trend = "up"
        elif slope < -0.05:
            trend = "down"
        else:
            trend = "stable"

        # 预计达标天数
        if slope > 0:
            predicted_days = max(1, ceil((target_score - current_score) / slope))
            predicted_date = (date.today() + timedelta(days=predicted_days)).isoformat()
        elif slope < -0.05:
            predicted_days = None
            predicted_date = None
        else:
            predicted_days = None
            predicted_date = None

        # 消息
        if trend == "down":
            message = "当前趋势下滑，建议增加学习时长和练习频率"
        elif predicted_days is None:
            message = "当前分数稳定，提升挑战难度可更快进步"
        elif predicted_days > 365:
            message = "目标较远，建议拆分为小里程碑逐步达成"
        elif predicted_days == 0:
            message = "已达成目标分数！"
        else:
            message = f"按当前节奏，预计 {predicted_days} 天后达标"

        # 持久化到 learning_predictions
        self._upsert_prediction(
            user_id, current_score, slope, target_score, predicted_days, predicted_date, db
        )

        return {
            "current_score": round(current_score, 1),
            "trend_slope": round(slope, 3),
            "target_score": target_score,
            "predicted_days": predicted_days,
            "predicted_date": predicted_date,
            "trend": trend,
            "message": message,
        }

    def check_alerts(self, user_id: int, db: Session) -> List[Dict]:
        """检查3条预警规则"""
        alerts = []

        # 规则1：连续3天未学习
        last_activity = self._get_last_activity_date(user_id, db)
        if last_activity:
            days_since = (date.today() - last_activity).days
            if days_since >= 3:
                alerts.append({
                    "type": "inactive",
                    "title": "连续未学习",
                    "message": f"你已经 {days_since} 天没有学习了，快来练习保持状态吧！",
                    "level": "warning",
                    "triggered": True,
                })
            else:
                alerts.append({
                    "type": "inactive",
                    "title": "连续未学习",
                    "message": "近3天有学习活动，继续保持",
                    "level": "info",
                    "triggered": False,
                })
        else:
            alerts.append({
                "type": "inactive",
                "title": "连续未学习",
                "message": "暂无学习记录",
                "level": "info",
                "triggered": False,
            })

        # 规则2：本周时长较上周下降 >50%
        this_week = self._get_weekly_activity_count(user_id, 0, db)
        last_week = self._get_weekly_activity_count(user_id, 1, db)
        if last_week > 0 and this_week < last_week * 0.5:
            alerts.append({
                "type": "duration_drop",
                "title": "学习时长下降",
                "message": f"本周学习活动较上周下降超过50%，记得保持学习节奏哦",
                "level": "warning",
                "triggered": True,
            })
        else:
            alerts.append({
                "type": "duration_drop",
                "title": "学习时长下降",
                "message": "学习节奏稳定",
                "level": "info",
                "triggered": False,
            })

        # 规则3：发音分连续7天未提升
        pron_improved = self._check_pronunciation_improvement(user_id, 7, db)
        if pron_improved is False:
            alerts.append({
                "type": "pronunciation_stagnant",
                "title": "发音停滞",
                "message": "发音得分连续7天未提升，建议尝试新的跟读内容或增加练习频率",
                "level": "info",
                "triggered": True,
            })
        else:
            alerts.append({
                "type": "pronunciation_stagnant",
                "title": "发音停滞",
                "message": "发音水平在持续进步",
                "level": "info",
                "triggered": False,
            })

        return alerts

    # ============================================================
    # 通知管理
    # ============================================================

    def create_notice(
        self, user_id: int, type: str, title: str, message: str,
        level: str, db: Session
    ) -> Notice:
        """创建通知"""
        notice = Notice(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            level=level,
        )
        db.add(notice)
        db.flush()
        return notice

    def get_notices(
        self, user_id: int, db: Session, unread_only: bool = False
    ) -> tuple:
        """获取通知列表"""
        query = db.query(Notice).filter(Notice.user_id == user_id)
        if unread_only:
            query = query.filter(Notice.is_read == False)
        notices = query.order_by(Notice.created_at.desc()).limit(50).all()

        unread_count = (
            db.query(func.count(Notice.id))
            .filter(Notice.user_id == user_id, Notice.is_read == False)
            .scalar()
        ) or 0

        items = [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "level": n.level,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notices
        ]

        return items, unread_count

    def mark_read(self, notice_id: int, user_id: int, db: Session) -> bool:
        """标记单条通知已读"""
        notice = (
            db.query(Notice)
            .filter(Notice.id == notice_id, Notice.user_id == user_id)
            .first()
        )
        if notice:
            notice.is_read = True
            db.flush()
            return True
        return False

    def mark_all_read(self, user_id: int, db: Session):
        """标记全部通知已读"""
        db.query(Notice).filter(
            Notice.user_id == user_id, Notice.is_read == False
        ).update({"is_read": True})
        db.flush()

    def get_unread_count(self, user_id: int, db: Session) -> int:
        """获取未读数量"""
        return (
            db.query(func.count(Notice.id))
            .filter(Notice.user_id == user_id, Notice.is_read == False)
            .scalar()
        ) or 0

    # ============================================================
    # 内部方法
    # ============================================================

    def _get_daily_composite_scores(
        self, user_id: int, days: int, db: Session
    ) -> List[tuple]:
        """获取最近N天每日综合分（发音×0.4+流利度×0.3+语法×0.3）"""
        start = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(
                func.date(UserSkillScore.created_at).label("d"),
                func.avg(UserSkillScore.score).label("avg"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= start,
            )
            .group_by(func.date(UserSkillScore.created_at))
            .order_by(func.date(UserSkillScore.created_at))
            .all()
        )
        return [(i, float(row[1])) for i, row in enumerate(rows)]

    def _get_target_score(self, user_id: int, db: Session) -> float:
        """获取用户目标分数"""
        pred = (
            db.query(LearningPrediction)
            .filter(LearningPrediction.user_id == user_id)
            .first()
        )
        return float(pred.target_score) if pred else 85.0

    def _upsert_prediction(
        self, user_id, current_score, slope, target_score,
        predicted_days, predicted_date, db
    ):
        """写入或更新预测记录"""
        pred = (
            db.query(LearningPrediction)
            .filter(LearningPrediction.user_id == user_id)
            .first()
        )
        if pred:
            pred.current_score = current_score
            pred.trend_slope = slope
            pred.target_score = target_score
            pred.predicted_days = predicted_days
            pred.predicted_date = predicted_date
        else:
            pred = LearningPrediction(
                user_id=user_id,
                current_score=current_score,
                trend_slope=slope,
                target_score=target_score,
                predicted_days=predicted_days,
                predicted_date=predicted_date,
            )
            db.add(pred)
        db.flush()

    def _get_last_activity_date(self, user_id: int, db: Session) -> Optional[date]:
        """获取最近活动日期"""
        row = (
            db.query(func.max(func.date(UserSkillScore.created_at)))
            .filter(UserSkillScore.user_id == user_id)
            .scalar()
        )
        return row

    def _get_weekly_activity_count(
        self, user_id: int, week_offset: int, db: Session
    ) -> int:
        """获取某周活动次数"""
        today = date.today()
        end = today - timedelta(days=week_offset * 7)
        start = end - timedelta(days=7)
        return (
            db.query(func.count(UserSkillScore.id))
            .filter(
                UserSkillScore.user_id == user_id,
                func.date(UserSkillScore.created_at) >= start,
                func.date(UserSkillScore.created_at) <= end,
            )
            .scalar()
        ) or 0

    def _check_pronunciation_improvement(
        self, user_id: int, days: int, db: Session
    ) -> Optional[bool]:
        """检查发音分是否在最近N天有提升"""
        end = datetime.utcnow()
        mid = end - timedelta(days=days // 2)
        start = end - timedelta(days=days)

        first_half = (
            db.query(func.avg(UserSkillScore.score))
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.dimension == "pronunciation",
                UserSkillScore.created_at >= start,
                UserSkillScore.created_at <= mid,
            )
            .scalar()
        )

        second_half = (
            db.query(func.avg(UserSkillScore.score))
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.dimension == "pronunciation",
                UserSkillScore.created_at >= mid,
                UserSkillScore.created_at <= end,
            )
            .scalar()
        )

        if first_half is None or second_half is None:
            return None  # 数据不足

        return float(second_half) > float(first_half)


# 单例
prediction_service = PredictionService()