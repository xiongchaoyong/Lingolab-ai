"""测评模块单元测试 — Schema 校验 + 核心算法"""

import pytest
from app.schemas.assessment import (
    QuestionItem,
    AssessmentStartResponse,
    AssessmentAnswerResponse,
    AssessmentSubmitResponse,
    CEFRLevel,
)


# 手动导入 assessment.py 中的纯函数（不触发数据库连接）
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 从 assessment.py 中提取纯函数进行测试
# 这些函数不依赖数据库，可以独立测试


# ============================================================
# Schema 校验测试
# ============================================================

class TestQuestionItem:
    """题目 Schema 校验"""

    def test_valid_question(self):
        q = QuestionItem(id=1, type="listening", difficulty="B1", content="What is this?")
        assert q.id == 1
        assert q.type == "listening"
        assert q.difficulty == "B1"

    def test_options_default_empty(self):
        q = QuestionItem(id=1, type="speaking", difficulty="B1", content="Describe...")
        assert q.options == []

    def test_options_for_multiple_choice(self):
        q = QuestionItem(
            id=1, type="grammar", difficulty="A2",
            content="Choose the correct answer",
            options=["A. go", "B. goes", "C. going", "D. gone"],
        )
        assert len(q.options) == 4

    def test_all_types_accepted(self):
        for t in ["listening", "speaking", "reading", "grammar"]:
            q = QuestionItem(id=1, type=t, difficulty="B1", content="test")
            assert q.type == t


class TestAssessmentStartResponse:
    """开始测评响应 Schema"""

    def test_valid_response(self):
        q = QuestionItem(id=1, type="listening", difficulty="B1", content="test")
        resp = AssessmentStartResponse(
            session_id="abc-123",
            question=q,
            total_questions=10,
            current_difficulty="B1",
        )
        assert resp.session_id == "abc-123"
        assert resp.total_questions == 10


class TestAssessmentAnswerResponse:
    """逐题提交响应 Schema"""

    def test_not_complete_with_next_question(self):
        q = QuestionItem(id=2, type="reading", difficulty="B1", content="next")
        resp = AssessmentAnswerResponse(
            complete=False,
            next_question=q,
            current_difficulty="B1",
        )
        assert resp.complete is False
        assert resp.next_question is not None

    def test_complete_without_next_question(self):
        resp = AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty="B2",
        )
        assert resp.complete is True
        assert resp.next_question is None


class TestCEFRLevel:
    """CEFR 等级 Schema"""

    def test_all_levels(self):
        for level, label in [("A1", "入门"), ("A2", "基础"), ("B1", "中级"),
                              ("B2", "中高级"), ("C1", "高级"), ("C2", "精通")]:
            ce = CEFRLevel(level=level, label=label)
            assert ce.level == level
            assert ce.label == label


class TestAssessmentSubmitResponse:
    """测评结果 Schema"""

    def test_valid_response(self):
        resp = AssessmentSubmitResponse(
            overall=75.5,
            cefr_level=CEFRLevel(level="B2", label="中高级"),
            dimension_scores={"listening": 80.0, "speaking": 70.0, "reading": 75.0, "grammar": 77.0},
            weakness={"dimension": "speaking", "score": 70.0, "label": "口语表达", "suggestion": "多练习"},
            duration=300,
        )
        assert resp.overall == 75.5
        assert resp.cefr_level.level == "B2"
        assert len(resp.dimension_scores) == 4
        assert resp.weakness["dimension"] == "speaking"


# ============================================================
# 核心算法测试 — 从 assessment.py 复制纯函数
# ============================================================

# 以下函数从 assessment.py 提取，避免导入触发数据库连接

CEFR_NUMERIC = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}
NUMERIC_CEFR = {v: k for k, v in CEFR_NUMERIC.items()}

CEFR_THRESHOLDS = [
    (96, "C2", "精通"),
    (81, "C1", "高级"),
    (61, "B2", "中高级"),
    (41, "B1", "中级"),
    (21, "A2", "基础"),
    (0, "A1", "入门"),
]


def _get_cefr(score: float) -> tuple:
    for threshold, level, label in CEFR_THRESHOLDS:
        if score >= threshold:
            return level, label
    return "A1", "入门"


def _level_to_cefr(level: float) -> str:
    rounded = round(level)
    rounded = max(1, min(6, rounded))
    return NUMERIC_CEFR[float(rounded)]


def _adjust_level(current: float, score: float) -> float:
    delta = 0.5 if score >= 60 else -0.5
    return max(1.0, min(6.0, current + delta))


class TestGetCEFR:
    """CEFR 定级算法"""

    def test_c2_threshold(self):
        level, label = _get_cefr(96)
        assert level == "C2"
        assert label == "精通"

    def test_c1_threshold(self):
        level, label = _get_cefr(81)
        assert level == "C1"

    def test_b2_threshold(self):
        level, label = _get_cefr(61)
        assert level == "B2"

    def test_b1_threshold(self):
        level, label = _get_cefr(41)
        assert level == "B1"

    def test_a2_threshold(self):
        level, label = _get_cefr(21)
        assert level == "A2"

    def test_a1_threshold(self):
        level, label = _get_cefr(0)
        assert level == "A1"

    def test_boundary_95_is_c1(self):
        level, _ = _get_cefr(95)
        assert level == "C1"

    def test_boundary_80_is_b2(self):
        level, _ = _get_cefr(80)
        assert level == "B2"

    def test_boundary_60_is_b1(self):
        level, _ = _get_cefr(60)
        assert level == "B1"

    def test_boundary_40_is_a2(self):
        level, _ = _get_cefr(40)
        assert level == "A2"

    def test_boundary_20_is_a1(self):
        level, _ = _get_cefr(20)
        assert level == "A1"

    def test_perfect_score(self):
        level, _ = _get_cefr(100)
        assert level == "C2"

    def test_zero_score(self):
        level, _ = _get_cefr(0)
        assert level == "A1"


class TestLevelToCEFR:
    """数值等级 → CEFR 等级转换"""

    def test_a1(self):
        assert _level_to_cefr(1.0) == "A1"

    def test_a2(self):
        assert _level_to_cefr(2.0) == "A2"

    def test_b1(self):
        assert _level_to_cefr(3.0) == "B1"

    def test_b2(self):
        assert _level_to_cefr(4.0) == "B2"

    def test_c1(self):
        assert _level_to_cefr(5.0) == "C1"

    def test_c2(self):
        assert _level_to_cefr(6.0) == "C2"

    def test_round_up(self):
        """3.6 → round → 4 → B2"""
        assert _level_to_cefr(3.6) == "B2"

    def test_round_down(self):
        """3.4 → round → 3 → B1"""
        assert _level_to_cefr(3.4) == "B1"

    def test_clamp_below_1(self):
        """低于 1.0 应钳制到 A1"""
        assert _level_to_cefr(0.5) == "A1"

    def test_clamp_above_6(self):
        """高于 6.0 应钳制到 C2"""
        assert _level_to_cefr(7.0) == "C2"


class TestAdjustLevel:
    """自适应难度调整"""

    def test_score_60_increases(self):
        """得分 60 → 升 0.5 级"""
        assert _adjust_level(3.0, 60) == 3.5

    def test_score_below_60_decreases(self):
        """得分 59 → 降 0.5 级"""
        assert _adjust_level(3.0, 59) == 2.5

    def test_score_100_increases(self):
        assert _adjust_level(3.0, 100) == 3.5

    def test_score_0_decreases(self):
        assert _adjust_level(3.0, 0) == 2.5

    def test_clamp_at_max_6(self):
        """已在 C2(6.0) 不再上升"""
        assert _adjust_level(6.0, 100) == 6.0

    def test_clamp_at_min_1(self):
        """已在 A1(1.0) 不再下降"""
        assert _adjust_level(1.0, 0) == 1.0

    def test_repeated_correct_raises_to_c2(self):
        """连续答对从 A1 升到 C2"""
        level = 1.0
        for _ in range(20):
            level = _adjust_level(level, 100)
        assert level == 6.0  # C2

    def test_repeated_wrong_drops_to_a1(self):
        """连续答错从 C2 降到 A1"""
        level = 6.0
        for _ in range(20):
            level = _adjust_level(level, 0)
        assert level == 1.0  # A1

    def test_alternating_stays_middle(self):
        """交替答对答错，难度在中间波动"""
        level = 3.0
        for _ in range(10):
            level = _adjust_level(level, 100)
            level = _adjust_level(level, 0)
        assert level == 3.0  # 回到原位


# ============================================================
# CEFR 数值映射完整性
# ============================================================

class TestCEFRMapping:
    """CEFR 数值映射表完整性"""

    def test_all_6_levels_exist(self):
        assert set(CEFR_NUMERIC.keys()) == {"A1", "A2", "B1", "B2", "C1", "C2"}

    def test_values_are_sequential(self):
        values = sorted(CEFR_NUMERIC.values())
        assert values == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

    def test_bidirectional_mapping(self):
        """NUMERIC_CEFR 是 CEFR_NUMERIC 的逆映射"""
        for k, v in CEFR_NUMERIC.items():
            assert NUMERIC_CEFR[v] == k
