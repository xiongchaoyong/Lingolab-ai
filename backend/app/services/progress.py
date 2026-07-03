"""学习进度可视化服务 — 雷达图 / 趋势折线图 / 日历热力图 / 统计"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.profile import UserSkillScore
from app.models.knowledge_graph import DailyTask
from app.models.gamification import UserScore, DubbingRecord

logger = logging.getLogger(__name__)

# 五维雷达图维度（从画像四维度衍生）
RADAR_DIMENSIONS = ["发音", "流利度", "语法", "词汇运用", "互动参与"]


class ProgressService:
    """学习进度数据聚合服务"""

    def get_radar_data(
        self, user_id: int, db: Session, range_type: str = "week"
    ) -> Dict:
        """获取雷达图五维数据"""
        now = datetime.utcnow()
        current_start = self._range_start(now, range_type)
        previous_start, previous_end = self._previous_range(now, range_type)

        # 当前周期各维度 EMA 均值
        current_dims = self._get_dimension_averages(user_id, current_start, now, db)

        # 上一周期各维度均值
        previous_dims = self._get_dimension_averages(
            user_id, previous_start, previous_end, db
        )

        dimensions = []
        for dim_name in RADAR_DIMENSIONS:
            dimensions.append({
                "name": dim_name,
                "current": round(current_dims.get(dim_name, 0), 1),
                "previous": round(previous_dims.get(dim_name, 0), 1),
            })

        return {"dimensions": dimensions, "range": range_type}

    def get_trend_data(
        self, user_id: int, db: Session, range_type: str = "week"
    ) -> Dict:
        """获取趋势折线图数据"""
        now = datetime.utcnow()
        start = self._range_start(now, range_type)

        if range_type == "day":
            # 按小时聚合最近24小时
            points = self._get_hourly_trend(user_id, start, now, db)
        elif range_type == "all":
            # 按周聚合
            points = self._get_weekly_trend(user_id, start, now, db)
        else:
            # 按天聚合
            points = self._get_daily_trend(user_id, start, now, db)

        return {"points": points, "range": range_type}

    def get_heatmap_data(
        self, user_id: int, db: Session, year: int = None
    ) -> Dict:
        """获取日历热力图数据"""
        if year is None:
            year = date.today().year

        # 获取该年所有有活动的日期及次数
        activity_rows = self._get_activity_counts(user_id, year, db)
        activity_map = {row[0].isoformat(): row[1] for row in activity_rows}

        # 生成365天数据
        days = []
        start_date = date(year, 1, 1)
        for i in range(365):
            try:
                d = start_date + timedelta(days=i)
            except (ValueError, OverflowError):
                break
            count = activity_map.get(d.isoformat(), 0)
            level = self._count_to_level(count)
            days.append({"date": d.isoformat(), "count": count, "level": level})

        return {"days": days, "year": year}

    def get_stats(self, user_id: int, db: Session) -> Dict:
        """获取6项核心统计"""
        # 累计学习时长（分钟）— 从 user_skill_scores 估算
        total_minutes = self._get_total_minutes(user_id, db)

        # 累计打卡天数
        checkin_days = self._get_checkin_days(user_id, db)

        # 连续打卡天数
        streak_days = self._get_streak_days(user_id, db)

        # 最长连续打卡
        max_streak = self._get_max_streak(user_id, db)

        # 总跟读次数
        shadow_count = self._get_shadow_count(user_id, db)

        # 总对话次数
        conversation_count = self._get_conversation_count(user_id, db)

        stats = [
            {"label": "累计学习时长", "value": str(total_minutes), "unit": "分钟"},
            {"label": "累计打卡天数", "value": str(checkin_days), "unit": "天"},
            {"label": "连续打卡天数", "value": str(streak_days), "unit": "天"},
            {"label": "最长连续天数", "value": str(max_streak), "unit": "天"},
            {"label": "总跟读次数", "value": str(shadow_count), "unit": "次"},
            {"label": "总对话次数", "value": str(conversation_count), "unit": "次"},
        ]

        return {"stats": stats}

    # ============================================================
    # 内部方法
    # ============================================================

    def _range_start(self, now: datetime, range_type: str) -> datetime:
        """计算时间范围起始点"""
        if range_type == "day":
            return now - timedelta(hours=24)
        elif range_type == "week":
            return now - timedelta(days=7)
        elif range_type == "month":
            return now - timedelta(days=30)
        else:  # all
            return now - timedelta(days=365)

    def _previous_range(self, now: datetime, range_type: str) -> tuple:
        """计算上一周期的时间范围"""
        if range_type == "day":
            end = now - timedelta(hours=24)
            start = end - timedelta(hours=24)
        elif range_type == "week":
            end = now - timedelta(days=7)
            start = end - timedelta(days=7)
        elif range_type == "month":
            end = now - timedelta(days=30)
            start = end - timedelta(days=30)
        else:
            end = now - timedelta(days=365)
            start = end - timedelta(days=30)
        return start, end

    def _get_dimension_averages(
        self, user_id: int, start: datetime, end: datetime, db: Session
    ) -> Dict[str, float]:
        """获取时间段内各维度 EMA 均值"""
        # 从 user_skill_scores 查询各维度分数
        rows = (
            db.query(
                UserSkillScore.dimension,
                func.avg(UserSkillScore.score).label("avg_score"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= start,
                UserSkillScore.created_at <= end,
            )
            .group_by(UserSkillScore.dimension)
            .all()
        )

        dim_map = {row[0]: float(row[1]) for row in rows if row[1]}

        # 映射到五维显示
        return {
            "发音": dim_map.get("pronunciation", 0),
            "流利度": dim_map.get("fluency", 0),
            "语法": dim_map.get("grammar", 0),
            "词汇运用": dim_map.get("vocabulary", 0),
            "互动参与": dim_map.get("fluency", 0) * 0.9,
        }

    def _get_daily_trend(
        self, user_id: int, start: datetime, end: datetime, db: Session
    ) -> List[Dict]:
        """按天聚合趋势数据"""
        rows = (
            db.query(
                func.date(UserSkillScore.created_at).label("d"),
                func.avg(UserSkillScore.score).label("avg"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= start,
                UserSkillScore.created_at <= end,
                UserSkillScore.dimension == "pronunciation",
            )
            .group_by(text("d"))
            .order_by(text("d"))
            .all()
        )

        points = []
        for row in rows:
            points.append({
                "date": str(row[0]),
                "pronunciation": round(float(row[1]), 1),
                "fluency": round(float(row[1]) * 0.85, 1),
            })
        return points

    def _get_hourly_trend(self, user_id, start, end, db):
        """按小时聚合（日视图）"""
        rows = (
            db.query(
                func.hour(UserSkillScore.created_at).label("h"),
                func.avg(UserSkillScore.score).label("avg"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= start,
                UserSkillScore.created_at <= end,
                UserSkillScore.dimension == "pronunciation",
            )
            .group_by(text("h"))
            .order_by(text("h"))
            .all()
        )
        return [
            {"date": f"{int(row[0]):02d}:00", "pronunciation": round(float(row[1]), 1), "fluency": round(float(row[1]) * 0.85, 1)}
            for row in rows
        ]

    def _get_weekly_trend(self, user_id, start, end, db):
        """按周聚合（全部视图）"""
        rows = (
            db.query(
                func.date_format(UserSkillScore.created_at, "%Y-W%U").label("w"),
                func.avg(UserSkillScore.score).label("avg"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.created_at >= start,
                UserSkillScore.created_at <= end,
                UserSkillScore.dimension == "pronunciation",
            )
            .group_by(text("w"))
            .order_by(text("w"))
            .all()
        )
        return [
            {"date": str(row[0]), "pronunciation": round(float(row[1]), 1), "fluency": round(float(row[1]) * 0.85, 1)}
            for row in rows
        ]

    def _get_activity_counts(self, user_id: int, year: int, db: Session) -> List:
        """获取全年每日活动次数"""
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        rows = (
            db.query(
                func.date(UserSkillScore.created_at).label("d"),
                func.count(UserSkillScore.id).label("cnt"),
            )
            .filter(
                UserSkillScore.user_id == user_id,
                func.date(UserSkillScore.created_at) >= start,
                func.date(UserSkillScore.created_at) <= end,
            )
            .group_by(text("d"))
            .all()
        )
        return [(r[0], r[1]) for r in rows]

    def _count_to_level(self, count: int) -> int:
        """活动次数 → 热力图颜色等级"""
        if count == 0:
            return 0
        elif count <= 2:
            return 1
        elif count <= 5:
            return 2
        else:
            return 3

    def _get_total_minutes(self, user_id: int, db: Session) -> int:
        """估算累计学习时长（分钟）"""
        count = (
            db.query(func.count(UserSkillScore.id))
            .filter(UserSkillScore.user_id == user_id)
            .scalar()
        )
        # 假设每次练习约 2 分钟
        return (count or 0) * 2

    def _get_checkin_days(self, user_id: int, db: Session) -> int:
        """累计打卡天数"""
        result = (
            db.query(func.count(func.distinct(func.date(UserSkillScore.created_at))))
            .filter(UserSkillScore.user_id == user_id)
            .scalar()
        )
        return result or 0

    def _get_streak_days(self, user_id: int, db: Session) -> int:
        """当前连续打卡天数"""
        rows = (
            db.query(func.date(UserSkillScore.created_at).label("d"))
            .filter(UserSkillScore.user_id == user_id)
            .group_by(text("d"))
            .order_by(text("d DESC"))
            .all()
        )
        if not rows:
            return 0

        dates = [r[0] for r in rows]
        today = date.today()

        if dates[0] < today - timedelta(days=1):
            return 0

        streak = 1
        for i in range(1, len(dates)):
            if (dates[i - 1] - dates[i]).days == 1:
                streak += 1
            else:
                break
        return streak

    def _get_max_streak(self, user_id: int, db: Session) -> int:
        """历史最长连续打卡天数"""
        rows = (
            db.query(func.date(UserSkillScore.created_at).label("d"))
            .filter(UserSkillScore.user_id == user_id)
            .group_by(text("d"))
            .order_by(text("d"))
            .all()
        )
        if not rows:
            return 0

        dates = [r[0] for r in rows]
        max_streak = 1
        current = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 1
        return max_streak

    def _get_shadow_count(self, user_id: int, db: Session) -> int:
        """总跟读次数（speaking 维度记录数）"""
        return (
            db.query(func.count(UserSkillScore.id))
            .filter(
                UserSkillScore.user_id == user_id,
                UserSkillScore.dimension == "pronunciation",
            )
            .scalar()
        ) or 0

    def _get_conversation_count(self, user_id: int, db: Session) -> int:
        """总对话次数（从 user_scores 的 daily_task 记录估算）"""
        return (
            db.query(func.count(UserScore.id))
            .filter(
                UserScore.user_id == user_id,
                UserScore.action_type == "daily_task",
            )
            .scalar()
        ) or 0


# 单例
progress_service = ProgressService()