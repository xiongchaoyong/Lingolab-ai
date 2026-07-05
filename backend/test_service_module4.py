"""服务模块4（激励服务）单元测试 — 游戏化 + 进度追踪 + 预测预警"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.gamification import (
    ChallengeLevelItem,
    DailyChallengeResponse,
    SubmitLevelResponse,
    CompleteChallengeResponse,
    DubbingContentItem,
    DubbingScoreResponse,
    DubbingRecordItem,
    BadgeItem,
    PointsRecord,
    PointsResponse,
    LeaderboardItem,
)
from app.schemas.progress import (
    RadarDimension,
    RadarResponse,
    TrendPoint,
    TrendResponse,
    HeatmapDay,
    HeatmapResponse,
    StatCardItem,
    StatsResponse,
)
from app.schemas.prediction import (
    PredictionData,
    AlertItem,
    AlertCheckResponse,
    NoticeItem,
    NoticesResponse,
    UnreadCountResponse,
)
from app.services.gamification import POINTS_RULES, BADGE_DEFINITIONS, DAILY_CHALLENGE_SENTENCES
from app.services.progress import RADAR_DIMENSIONS


# ============================================================
# 游戏化 Schema
# ============================================================

class TestChallengeSchemas:
    """闯关 Schema 验证"""

    def test_challenge_level(self):
        level = ChallengeLevelItem(level=1, text="Hello", difficulty="A1", pass_score=70)
        assert level.level == 1
        assert level.pass_score == 70

    def test_daily_challenge_response(self):
        resp = DailyChallengeResponse(
            levels=[ChallengeLevelItem(level=i, text=f"text{i}", difficulty="A1") for i in range(1, 6)],
            date="2026-06-26",
            completed=False,
            current_level=1,
            level_scores={},
        )
        assert len(resp.levels) == 5
        assert resp.completed is False

    def test_submit_level_response(self):
        resp = SubmitLevelResponse(level=1, score=85.5, passed=True, dimensions={"音素准确度": 80})
        assert resp.passed is True
        assert resp.score == 85.5

    def test_complete_challenge_response(self):
        resp = CompleteChallengeResponse(
            levels_passed=5, points_earned=130, total_points=500,
            new_badges=[BadgeItem(badge_type="scholar", badge_name="学霸成就", earned=True)],
        )
        assert resp.levels_passed == 5
        assert resp.points_earned == 130
        assert len(resp.new_badges) == 1


class TestDubbingSchemas:
    """配音 Schema 验证"""

    def test_dubbing_content(self):
        item = DubbingContentItem(id=1, title="Friends", difficulty="easy", duration=30, subtitle="Hello!")
        assert item.id == 1

    def test_dubbing_score(self):
        resp = DubbingScoreResponse(
            content_id=1, pronunciation_score=85, intonation_score=78,
            emotion_score=80, total_score=81, points_earned=30,
        )
        assert resp.total_score == 81

    def test_dubbing_record(self):
        from datetime import datetime
        item = DubbingRecordItem(id=1, content_title="Friends", total_score=85.0, created_at=datetime.now())
        assert item.content_title == "Friends"


class TestPointsBadgeSchemas:
    """积分与勋章 Schema 验证"""

    def test_badge_item(self):
        badge = BadgeItem(badge_type="streak", badge_name="坚持之星", description="连续打卡7天", earned=True)
        assert badge.earned is True

    def test_points_record(self):
        from datetime import datetime
        rec = PointsRecord(id=1, action_type="challenge_level", score=20, description="闯关通过", created_at=datetime.now())
        assert rec.score == 20

    def test_points_response(self):
        resp = PointsResponse(total_points=500, recent_records=[])
        assert resp.total_points == 500

    def test_leaderboard_item(self):
        item = LeaderboardItem(rank=1, user_id=1, username="test", total_points=1000, badge_count=5)
        assert item.rank == 1
        assert item.badge_count == 5


# ============================================================
# 游戏化常量
# ============================================================

class TestGamificationConstants:
    """游戏化常量验证"""

    def test_points_rules_count(self):
        """8 种积分规则"""
        assert len(POINTS_RULES) == 8

    def test_points_rules_values(self):
        """积分值均为正数"""
        for action, points in POINTS_RULES.items():
            assert points > 0, f"{action} 积分应为正数"

    def test_badge_definitions_count(self):
        """7 枚勋章"""
        assert len(BADGE_DEFINITIONS) == 7

    def test_badge_definitions_fields(self):
        """每枚勋章都有 name + description"""
        for badge_type, info in BADGE_DEFINITIONS.items():
            assert "name" in info
            assert "description" in info
            assert len(info["name"]) > 0

    def test_daily_challenge_levels(self):
        """5 关闯关"""
        assert len(DAILY_CHALLENGE_SENTENCES) == 5

    def test_daily_challenge_difficulty_progression(self):
        """难度递增"""
        difficulties = [s["difficulty"] for s in DAILY_CHALLENGE_SENTENCES]
        # A1 → A2 → B1 → B1 → B2
        assert difficulties[0] == "A1"
        assert difficulties[-1] == "B2"

    def test_daily_challenge_pass_score(self):
        """所有关卡通过分数均为 70"""
        for s in DAILY_CHALLENGE_SENTENCES:
            assert s["pass_score"] == 70


# ============================================================
# 进度可视化 Schema
# ============================================================

class TestRadarSchemas:
    """雷达图 Schema 验证"""

    def test_radar_dimension(self):
        d = RadarDimension(name="发音准确率", current=80.5, previous=75.0)
        assert d.current == 80.5

    def test_radar_response(self):
        resp = RadarResponse(
            dimensions=[RadarDimension(name=f"dim{i}", current=80, previous=70) for i in range(4)],
            range="week",
        )
        assert len(resp.dimensions) == 4

    def test_four_radar_dimensions(self):
        """四维雷达图维度"""
        expected = ["发音", "流利度", "语法", "词汇运用"]
        assert RADAR_DIMENSIONS == expected


class TestTrendSchemas:
    """趋势图 Schema 验证"""

    def test_trend_point(self):
        p = TrendPoint(date="2026-06-26", pronunciation=80, fluency=75)
        assert p.date == "2026-06-26"

    def test_trend_response(self):
        resp = TrendResponse(
            points=[TrendPoint(date=f"2026-06-{i}", pronunciation=80, fluency=75) for i in range(1, 8)],
            range="week",
        )
        assert len(resp.points) == 7


class TestHeatmapSchemas:
    """热力图 Schema 验证"""

    def test_heatmap_day(self):
        d = HeatmapDay(date="2026-06-26", count=3, level=2)
        assert d.count == 3
        assert d.level == 2

    def test_heatmap_response(self):
        resp = HeatmapResponse(
            days=[HeatmapDay(date=f"2026-01-{i:02d}", count=i % 4, level=min(i % 4, 3)) for i in range(1, 32)],
            year=2026,
        )
        assert len(resp.days) == 31
        assert resp.year == 2026


class TestStatsSchemas:
    """统计 Schema 验证"""

    def test_stat_card(self):
        card = StatCardItem(label="总学习时长", value="12", unit="小时")
        assert card.value == "12"

    def test_stats_response(self):
        resp = StatsResponse(stats=[
            StatCardItem(label="总学习时长", value="12", unit="小时"),
            StatCardItem(label="完成任务", value="30", unit="个"),
            StatCardItem(label="连续打卡", value="7", unit="天"),
        ])
        assert len(resp.stats) == 3


# ============================================================
# 预测预警 Schema
# ============================================================

class TestPredictionSchemas:
    """预测 Schema 验证"""

    def test_prediction_data(self):
        data = PredictionData(
            current_score=75.0, trend_slope=0.5, target_score=85.0,
            predicted_days=20, predicted_date="2026-07-16", trend="up",
            message="按当前进度，预计 20 天后达标",
        )
        assert data.current_score == 75.0
        assert data.trend == "up"
        assert data.predicted_days == 20

    def test_prediction_stable(self):
        data = PredictionData(current_score=60.0, target_score=80.0, trend="stable", message="进度较慢")
        assert data.trend_slope is None
        assert data.predicted_days is None


class TestAlertSchemas:
    """预警 Schema 验证"""

    def test_alert_item(self):
        alert = AlertItem(
            type="inactivity", title="连续未学习",
            message="您已连续 3 天未学习", level="warning", triggered=True,
        )
        assert alert.triggered is True
        assert alert.level == "warning"

    def test_alert_check_response(self):
        resp = AlertCheckResponse(alerts=[
            AlertItem(type="inactivity", title="t", message="m", level="warning"),
            AlertItem(type="decline", title="t", message="m", level="warning"),
        ])
        assert len(resp.alerts) == 2


class TestNoticeSchemas:
    """通知 Schema 验证"""

    def test_notice_item(self):
        from datetime import datetime
        notice = NoticeItem(
            id=1, type="alert", title="预警", message="内容",
            level="warning", is_read=False, created_at=datetime.now(),
        )
        assert notice.is_read is False

    def test_notices_response(self):
        resp = NoticesResponse(notices=[], unread_count=3)
        assert resp.unread_count == 3

    def test_unread_count(self):
        resp = UnreadCountResponse(unread_count=5)
        assert resp.unread_count == 5
