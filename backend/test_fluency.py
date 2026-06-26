"""流利度模块单元测试 — 五维算法边界 + 汇总逻辑"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.fluency import (
    _get_fluency_grade,
    _count_words,
    _detect_repetitions,
    assess_algorithmic,
    aggregate_fluency,
)


# ============================================================
# 语速评分边界（维度1，满分 25）
# ============================================================

class TestWMPScore:
    """语速评分边界测试"""

    def _calc_wpm_score(self, text, words, duration):
        result = assess_algorithmic(text, words, duration)
        return result["wpm"]["score"], result["wpm"]["value"]

    def test_ideal_110wpm(self):
        """理想语速 110 wpm → 满分"""
        # 22 words in 12 seconds = 110 wpm
        words = [{"word": f"w{i}", "start": i * 0.545, "end": i * 0.545 + 0.3} for i in range(22)]
        text = " ".join(f"w{i}" for i in range(22))
        score, wpm = self._calc_wpm_score(text, words, 12.5)
        assert score == 25
        assert 100 <= wpm <= 120

    def test_slow_50wpm(self):
        """语速 50 wpm → 约 12 分"""
        words = [{"word": f"w{i}", "start": i * 1.2, "end": i * 1.2 + 0.5} for i in range(10)]
        text = " ".join(f"w{i}" for i in range(10))
        score, wpm = self._calc_wpm_score(text, words, 12.0)
        assert wpm < 100
        assert score < 25

    def test_fast_200wpm(self):
        """语速 200 wpm → 被惩罚"""
        words = [{"word": f"w{i}", "start": i * 0.3, "end": i * 0.3 + 0.1} for i in range(30)]
        text = " ".join(f"w{i}" for i in range(30))
        score, wpm = self._calc_wpm_score(text, words, 9.0)
        assert wpm > 120
        assert score < 25

    def test_zero_duration_fallback(self):
        """时长为 0 的兜底"""
        words = [{"word": "hi", "start": 0, "end": 0}]
        score, wpm = self._calc_wpm_score("hi", words, 0)
        assert score >= 0


# ============================================================
# 停顿评分边界（维度2，满分 20）
# ============================================================

class TestPauseScore:
    """停顿评分边界测试"""

    def _calc_pause_score(self, words, duration):
        text = " ".join(w["word"] for w in words)
        result = assess_algorithmic(text, words, duration)
        return result["pause_frequency"]["score"], result["pause_frequency"]["pauses_per_min"]

    def test_no_pauses(self):
        """无停顿 → 满分"""
        words = [
            {"word": "a", "start": 0, "end": 0.3},
            {"word": "b", "start": 0.4, "end": 0.7},
            {"word": "c", "start": 0.8, "end": 1.1},
        ]
        score, ppm = self._calc_pause_score(words, 1.5)
        assert score == 20
        assert ppm <= 2

    def test_few_pauses(self):
        """少量停顿 → 16 分"""
        words = [
            {"word": "a", "start": 0, "end": 0.3},
            {"word": "b", "start": 1.0, "end": 1.3},  # 0.7s gap
            {"word": "c", "start": 1.4, "end": 1.7},
        ]
        score, ppm = self._calc_pause_score(words, 2.0)
        assert score <= 16

    def test_many_pauses(self):
        """大量停顿 → 低分"""
        words = [
            {"word": "a", "start": 0, "end": 0.3},
            {"word": "b", "start": 2.0, "end": 2.3},
            {"word": "c", "start": 4.0, "end": 4.3},
            {"word": "d", "start": 6.0, "end": 6.3},
        ]
        score, ppm = self._calc_pause_score(words, 7.0)
        assert ppm > 5
        assert score < 16


# ============================================================
# 重复检测边界（维度3，满分 20）
# ============================================================

class TestRepetitionEdgeCases:
    """重复检测边界测试"""

    def test_no_repetition(self):
        assert _detect_repetitions("the quick brown fox jumps over lazy dog") == 0.0

    def test_short_text_skipped(self):
        """2 个词以下不检测"""
        assert _detect_repetitions("hello hello") == 0.0

    def test_three_words_minimal(self):
        """恰好 3 个词开始检测"""
        rate = _detect_repetitions("hello hello world")
        assert rate > 0

    def test_perfectly_fluent(self):
        """完全流利无重复"""
        assert _detect_repetitions("I went to the store and bought some milk") == 0.0

    def test_heavy_repetition(self):
        """严重重复"""
        rate = _detect_repetitions("the the the the the the the the")
        assert rate > 0.5


# ============================================================
# 综合评分结构验证
# ============================================================

class TestAssessAlgorithmicStructure:
    """算法流利度输出结构"""

    def test_output_keys(self):
        words = [{"word": "hello", "start": 0, "end": 0.5}]
        result = assess_algorithmic("hello", words, 1.0)

        assert "wpm" in result
        assert "pause_frequency" in result
        assert "repetition" in result
        assert "overall" in result

    def test_wpm_structure(self):
        words = [{"word": "hello", "start": 0, "end": 0.5}]
        result = assess_algorithmic("hello", words, 1.0)

        wpm = result["wpm"]
        assert "score" in wpm
        assert "value" in wpm
        assert "max" in wpm
        assert "label" in wpm
        assert "detail" in wpm
        assert wpm["max"] == 25

    def test_pause_structure(self):
        words = [{"word": "hello", "start": 0, "end": 0.5}]
        result = assess_algorithmic("hello", words, 1.0)

        pause = result["pause_frequency"]
        assert "score" in pause
        assert "pauses_per_min" in pause
        assert "pause_count" in pause
        assert "max" in pause
        assert pause["max"] == 20

    def test_repetition_structure(self):
        words = [{"word": "hello", "start": 0, "end": 0.5}]
        result = assess_algorithmic("hello", words, 1.0)

        rep = result["repetition"]
        assert "score" in rep
        assert "rate" in rep
        assert "max" in rep
        assert rep["max"] == 20

    def test_overall_max_65(self):
        """算法维度满分 65"""
        words = [
            {"word": f"w{i}", "start": i * 0.55, "end": i * 0.55 + 0.3}
            for i in range(20)
        ]
        text = " ".join(f"w{i}" for i in range(20))
        result = assess_algorithmic(text, words, 11.0)
        assert result["overall"] <= 65


# ============================================================
# 多轮汇总边界
# ============================================================

class TestAggregateFluencyEdgeCases:
    """多轮汇总边界测试"""

    def test_empty_returns_zero(self):
        result = aggregate_fluency([])
        assert result["overall"] == 0
        assert result["grade"] == "入门"
        assert result["best_round"] is None

    def test_single_round_no_llm(self):
        """无 LLM 评分的单轮"""
        rounds = [{
            "text": "hello",
            "wpm": {"score": 20},
            "pause_frequency": {"score": 18},
            "repetition": {"score": 19},
        }]
        result = aggregate_fluency(rounds)
        assert result["overall"] == 57  # 20+18+19+0+0
        assert result["best_round"] == 1

    def test_single_round_with_llm(self):
        """有 LLM 评分的单轮"""
        rounds = [{
            "text": "hello",
            "wpm": {"score": 25},
            "pause_frequency": {"score": 20},
            "repetition": {"score": 20},
            "llm": {
                "grammar": {"score": 20},
                "relevance": {"score": 15},
            },
        }]
        result = aggregate_fluency(rounds)
        assert result["overall"] == 100  # 25+20+20+20+15
        assert result["grade"] == "优秀"

    def test_multiple_rounds_best_round(self):
        """多轮中最佳轮次识别"""
        rounds = [
            {"text": "weak", "wpm": {"score": 10}, "pause_frequency": {"score": 10}, "repetition": {"score": 10}},
            {"text": "best", "wpm": {"score": 25}, "pause_frequency": {"score": 20}, "repetition": {"score": 20}},
            {"text": "mid", "wpm": {"score": 15}, "pause_frequency": {"score": 15}, "repetition": {"score": 15}},
        ]
        result = aggregate_fluency(rounds)
        assert result["best_round"] == 2

    def test_dimension_averages(self):
        """维度平均值计算"""
        rounds = [
            {"wpm": {"score": 20}, "pause_frequency": {"score": 18}, "repetition": {"score": 19}},
            {"wpm": {"score": 22}, "pause_frequency": {"score": 16}, "repetition": {"score": 18}},
        ]
        result = aggregate_fluency(rounds)
        assert result["dimension_averages"]["wpm_avg"] == 21.0
        assert result["dimension_averages"]["pause_avg"] == 17.0
        assert result["dimension_averages"]["repetition_avg"] == 18.5
