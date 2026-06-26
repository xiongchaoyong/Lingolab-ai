"""智能对话模块单元测试 — 流利度算法 + Schema 校验"""

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
from app.schemas.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationSpeakResponse,
    ConversationEndResponse,
)


# ============================================================
# 流利度算法测试
# ============================================================

class TestGetFluencyGrade:
    """流利度分段评级"""

    def test_excellent(self):
        assert _get_fluency_grade(85) == "优秀"
        assert _get_fluency_grade(100) == "优秀"

    def test_good(self):
        assert _get_fluency_grade(70) == "良好"
        assert _get_fluency_grade(84) == "良好"

    def test_medium(self):
        assert _get_fluency_grade(55) == "中等"
        assert _get_fluency_grade(69) == "中等"

    def test_beginner(self):
        assert _get_fluency_grade(40) == "初级"
        assert _get_fluency_grade(54) == "初级"

    def test_entry(self):
        assert _get_fluency_grade(0) == "入门"
        assert _get_fluency_grade(39) == "入门"

    def test_boundary_85(self):
        assert _get_fluency_grade(85) == "优秀"
        assert _get_fluency_grade(84) == "良好"

    def test_boundary_70(self):
        assert _get_fluency_grade(70) == "良好"
        assert _get_fluency_grade(69) == "中等"

    def test_boundary_55(self):
        assert _get_fluency_grade(55) == "中等"
        assert _get_fluency_grade(54) == "初级"

    def test_boundary_40(self):
        assert _get_fluency_grade(40) == "初级"
        assert _get_fluency_grade(39) == "入门"


class TestCountWords:
    """单词计数"""

    def test_normal_sentence(self):
        assert _count_words("hello world how are you") == 5

    def test_single_word(self):
        assert _count_words("hello") == 1

    def test_empty_string(self):
        assert _count_words("") == 0  # "".split() == []

    def test_whitespace_only(self):
        assert _count_words("   ") == 0

    def test_extra_spaces(self):
        assert _count_words("  hello   world  ") == 2

    def test_newlines_and_tabs(self):
        assert _count_words("hello\nworld\thow") == 3


class TestDetectRepetitions:
    """重复检测"""

    def test_no_repetition(self):
        assert _detect_repetitions("I like to eat apples") == 0.0

    def test_short_text_no_detection(self):
        """少于 3 个词不检测"""
        assert _detect_repetitions("hello hello") == 0.0

    def test_consecutive_repetition(self):
        """连续重复词"""
        rate = _detect_repetitions("I I I went to the store")
        assert rate > 0

    def test_no_repetition_long_text(self):
        rate = _detect_repetitions("the quick brown fox jumps over the lazy dog")
        assert rate >= 0  # "the" appears twice but not consecutively

    def test_all_same_words(self):
        rate = _detect_repetitions("hello hello hello hello hello")
        assert rate > 0.5

    def test_returns_float(self):
        assert isinstance(_detect_repetitions("one two three four five"), float)


class TestAssessAlgorithmic:
    """算法流利度评估"""

    def test_ideal_speech(self):
        """理想语速 110 wpm，无停顿，无重复"""
        words = [
            {"word": f"word{i}", "start": i * 0.55, "end": i * 0.55 + 0.3}
            for i in range(20)
        ]
        # 20 words in ~10.45 seconds ≈ 115 wpm
        text = " ".join(f"word{i}" for i in range(20))
        result = assess_algorithmic(text, words, 11.0)

        assert result["wpm"]["score"] == 25  # ideal range
        assert result["pause_frequency"]["score"] == 20  # no pauses > 0.5s
        assert result["repetition"]["score"] == 20  # no repetition
        assert result["overall"] == 65  # 25 + 20 + 20

    def test_slow_speech(self):
        """语速过慢 ~50 wpm"""
        words = [
            {"word": f"word{i}", "start": i * 1.2, "end": i * 1.2 + 0.5}
            for i in range(10)
        ]
        text = " ".join(f"word{i}" for i in range(10))
        # 10 words in ~10.8 seconds ≈ 55 wpm
        result = assess_algorithmic(text, words, 12.0)

        assert result["wpm"]["score"] < 25  # below ideal
        assert result["wpm"]["value"] < 100

    def test_fast_speech(self):
        """语速过快 ~200 wpm"""
        words = [
            {"word": f"word{i}", "start": i * 0.3, "end": i * 0.3 + 0.1}
            for i in range(30)
        ]
        text = " ".join(f"word{i}" for i in range(30))
        # 30 words in ~8.7 seconds ≈ 207 wpm
        result = assess_algorithmic(text, words, 9.0)

        assert result["wpm"]["score"] < 25  # penalized for being too fast

    def test_many_pauses(self):
        """大量停顿"""
        words = [
            {"word": "hello", "start": 0, "end": 0.3},
            {"word": "world", "start": 2.0, "end": 2.5},  # 1.7s gap
            {"word": "how", "start": 4.0, "end": 4.3},  # 1.5s gap
            {"word": "are", "start": 6.0, "end": 6.3},  # 1.7s gap
            {"word": "you", "start": 8.0, "end": 8.3},  # 1.7s gap
        ]
        result = assess_algorithmic("hello world how are you", words, 9.0)

        assert result["pause_frequency"]["pauses_per_min"] > 2
        assert result["pause_frequency"]["score"] < 20

    def test_no_words_fallback(self):
        """无词级时间戳时的兜底"""
        result = assess_algorithmic("hello world", [], 5.0)

        assert result["wpm"]["value"] >= 0
        assert result["overall"] >= 0

    def test_output_structure(self):
        """输出结构完整性"""
        words = [{"word": "hello", "start": 0, "end": 0.5}]
        result = assess_algorithmic("hello", words, 1.0)

        assert "wpm" in result
        assert "pause_frequency" in result
        assert "repetition" in result
        assert "overall" in result
        assert "score" in result["wpm"]
        assert "max" in result["wpm"]
        assert result["wpm"]["max"] == 25
        assert result["pause_frequency"]["max"] == 20
        assert result["repetition"]["max"] == 20

    def test_overall_max_65(self):
        """算法维度满分 65（25+20+20）"""
        words = [
            {"word": f"w{i}", "start": i * 0.55, "end": i * 0.55 + 0.3}
            for i in range(20)
        ]
        text = " ".join(f"w{i}" for i in range(20))
        result = assess_algorithmic(text, words, 11.0)

        assert result["overall"] <= 65


class TestAggregateFluency:
    """多轮流利度汇总"""

    def test_empty_rounds(self):
        result = aggregate_fluency([])
        assert result["overall"] == 0
        assert result["grade"] == "入门"
        assert result["rounds"] == []
        assert result["best_round"] is None

    def test_single_round(self):
        round_scores = [{
            "text": "hello world",
            "wpm": {"score": 20},
            "pause_frequency": {"score": 18},
            "repetition": {"score": 19},
        }]
        result = aggregate_fluency(round_scores)

        assert result["overall"] == 57  # 20 + 18 + 19
        assert result["grade"] == "中等"
        assert len(result["rounds"]) == 1
        assert result["best_round"] == 1

    def test_multiple_rounds(self):
        round_scores = [
            {
                "text": "round one",
                "wpm": {"score": 20},
                "pause_frequency": {"score": 18},
                "repetition": {"score": 19},
                "llm": {
                    "grammar": {"score": 15},
                    "relevance": {"score": 10},
                },
            },
            {
                "text": "round two",
                "wpm": {"score": 22},
                "pause_frequency": {"score": 16},
                "repetition": {"score": 18},
                "llm": {
                    "grammar": {"score": 18},
                    "relevance": {"score": 12},
                },
            },
        ]
        result = aggregate_fluency(round_scores)

        # Round 1: 20+18+19+15+10 = 82
        # Round 2: 22+16+18+18+12 = 86
        # Overall: (82+86)/2 = 84
        assert result["overall"] == 84
        assert result["grade"] == "良好"
        assert result["best_round"] == 2

    def test_best_round_detection(self):
        """最佳轮次检测"""
        round_scores = [
            {"text": "weak", "wpm": {"score": 10}, "pause_frequency": {"score": 10}, "repetition": {"score": 10}},
            {"text": "strong", "wpm": {"score": 25}, "pause_frequency": {"score": 20}, "repetition": {"score": 20}},
            {"text": "medium", "wpm": {"score": 15}, "pause_frequency": {"score": 15}, "repetition": {"score": 15}},
        ]
        result = aggregate_fluency(round_scores)
        assert result["best_round"] == 2

    def test_dimension_averages(self):
        round_scores = [
            {"wpm": {"score": 20}, "pause_frequency": {"score": 18}, "repetition": {"score": 19}},
            {"wpm": {"score": 22}, "pause_frequency": {"score": 16}, "repetition": {"score": 18}},
        ]
        result = aggregate_fluency(round_scores)

        assert result["dimension_averages"]["wpm_avg"] == 21.0
        assert result["dimension_averages"]["pause_avg"] == 17.0
        assert result["dimension_averages"]["repetition_avg"] == 18.5

    def test_grade_mapping(self):
        """综合分映射到正确评级"""
        # 构造一个高分轮次
        high_score = [{
            "wpm": {"score": 25},
            "pause_frequency": {"score": 20},
            "repetition": {"score": 20},
            "llm": {"grammar": {"score": 20}, "relevance": {"score": 15}},
        }]
        result = aggregate_fluency(high_score)
        assert result["overall"] == 100
        assert result["grade"] == "优秀"


# ============================================================
# Schema 校验测试
# ============================================================

class TestConversationStartRequest:
    """对话开始请求 Schema"""

    def test_default_values(self):
        req = ConversationStartRequest()
        assert req.scene == "self_intro"
        assert req.cefr_level == "B1"

    def test_custom_values(self):
        req = ConversationStartRequest(scene="restaurant", cefr_level="A2")
        assert req.scene == "restaurant"
        assert req.cefr_level == "A2"


class TestConversationStartResponse:
    """对话开始响应 Schema"""

    def test_valid_response(self):
        resp = ConversationStartResponse(
            session_id="abc123",
            ai_text="Hello! Tell me about yourself.",
        )
        assert resp.session_id == "abc123"
        assert resp.ai_audio_base64 == ""  # default


class TestConversationSpeakResponse:
    """对话说话响应 Schema"""

    def test_basic_response(self):
        resp = ConversationSpeakResponse(
            user_text="I am a student",
            ai_text="That's great!",
        )
        assert resp.conversation_complete is False  # default
        assert resp.grammar_correction is None  # default

    def test_with_grammar_correction(self):
        resp = ConversationSpeakResponse(
            user_text="I goed to school",
            ai_text="I see!",
            grammar_correction={
                "original": "I goed",
                "correction": "I went",
                "tip": "go → went (irregular verb)",
            },
        )
        assert resp.grammar_correction["original"] == "I goed"

    def test_conversation_complete(self):
        resp = ConversationSpeakResponse(
            user_text="bye",
            ai_text="Goodbye!",
            conversation_complete=True,
        )
        assert resp.conversation_complete is True


class TestConversationEndResponse:
    """对话结束响应 Schema"""

    def test_valid_response(self):
        resp = ConversationEndResponse(
            overall=78.5,
            pronunciation=[{"label": "音素准确度", "score": 80}],
            text_dimensions=[{"label": "语法正确率", "score": 75}],
            suggestions="Keep practicing!",
        )
        assert resp.overall == 78.5
        assert len(resp.pronunciation) == 1
        assert resp.fluency is None  # default

    def test_with_fluency(self):
        resp = ConversationEndResponse(
            overall=80,
            fluency={"overall": 75, "grade": "良好"},
        )
        assert resp.fluency["grade"] == "良好"

    def test_default_empty_lists(self):
        resp = ConversationEndResponse(overall=0)
        assert resp.pronunciation == []
        assert resp.text_dimensions == []
        assert resp.utterances == []
        assert resp.transcript == []
