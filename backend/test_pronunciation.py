"""发音评测模块单元测试 — Schema 验证 + 评分权重 + 音素建议"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.pronunciation import (
    DimensionScore,
    PronunciationError,
    CharScore,
    F0Point,
    StressVizData,
    IntonationVizData,
    AnalysisDetail,
    RhythmVizData,
    LinkingPair,
    LinkingVizData,
    PronunciationResponse,
    ContentItem,
    RecordItem,
)
from app.services.pronunciation import PHONEME_TIPS


# ============================================================
# Schema 验证
# ============================================================

class TestDimensionScoreSchema:
    """DimensionScore 字段验证"""

    def test_valid(self):
        d = DimensionScore(label="音素准确度", score=85.5)
        assert d.label == "音素准确度"
        assert d.score == 85.5

    def test_five_dimensions(self):
        """五维评分标签"""
        labels = ["音素准确度", "重音位置", "语调曲线", "连读表现", "节奏感"]
        for label in labels:
            d = DimensionScore(label=label, score=80)
            assert d.label == label


class TestPronunciationErrorSchema:
    """PronunciationError 字段验证"""

    def test_valid(self):
        err = PronunciationError(
            phoneme="TH", actual="T", tip="舌尖轻触上齿", score=30.0
        )
        assert err.phoneme == "TH"
        assert err.actual == "T"
        assert err.tip == "舌尖轻触上齿"
        assert err.score == 30.0


class TestVisualizationSchemas:
    """可视化数据 Schema 验证"""

    def test_stress_viz(self):
        viz = StressVizData(
            chars=["h", "e", "l", "o"],
            energies=[0.5, 0.8, 0.3, 0.6],
            durations=[100, 120, 80, 110],
            is_stressed=[False, True, False, False],
            energy_cv=0.25,
            dur_cv=0.15,
        )
        assert len(viz.chars) == 4
        assert viz.energy_cv == 0.25

    def test_intonation_viz(self):
        viz = IntonationVizData(
            direction="falling",
            range_st=5.0,
            f0_points=[F0Point(t=0.0, hz=200), F0Point(t=1.0, hz=150)],
            sentence_type="statement",
            slope_st_per_sec=-2.5,
        )
        assert viz.direction == "falling"
        assert len(viz.f0_points) == 2

    def test_rhythm_viz(self):
        viz = RhythmVizData(
            durations_ms=[50, 60, 55, 200],
            chars=["h", "e", "l", "o"],
            mean_ms=91.25,
            std_ms=62.5,
            cv=0.685,
            pause_count=1,
            is_pause=[False, False, False, True],
        )
        assert viz.pause_count == 1
        assert viz.is_pause[3] is True

    def test_linking_pair(self):
        pair = LinkingPair(
            word_pair="not at",
            linkable=True,
            last_phoneme="T",
            first_phoneme="AE",
            gap_ms=25.0,
            score=85.0,
        )
        assert pair.linkable is True
        assert pair.score == 85.0

    def test_linking_viz(self):
        viz = LinkingVizData(
            pairs=[
                LinkingPair(word_pair="not at", linkable=True, gap_ms=25.0, score=85.0),
                LinkingPair(word_pair="pick it", linkable=True, gap_ms=40.0, score=60.0),
            ],
            linkable_count=2,
            linked_count=1,
            avg_gap_ms=32.5,
        )
        assert viz.linkable_count == 2
        assert viz.linked_count == 1


class TestPronunciationResponseSchema:
    """PronunciationResponse 完整响应验证"""

    def test_full_response(self):
        resp = PronunciationResponse(
            overall=82.5,
            dimensions=[
                DimensionScore(label="音素准确度", score=85),
                DimensionScore(label="重音位置", score=80),
                DimensionScore(label="语调曲线", score=78),
                DimensionScore(label="连读表现", score=82),
                DimensionScore(label="节奏感", score=80),
            ],
            errors=[PronunciationError(phoneme="TH", actual="T", tip="舌尖轻触上齿")],
            char_scores=[],
            analysis_detail=AnalysisDetail(stress="good", intonation="falling", linking="ok"),
        )
        assert resp.overall == 82.5
        assert len(resp.dimensions) == 5
        assert len(resp.errors) == 1

    def test_minimal_response(self):
        resp = PronunciationResponse(
            overall=50.0,
            dimensions=[DimensionScore(label="音素准确度", score=50)],
            errors=[],
        )
        assert resp.overall == 50.0
        assert resp.stress_viz is None
        assert resp.intonation_viz is None


# ============================================================
# 评分权重验证
# ============================================================

class TestScoringWeights:
    """模式加权综合分验证"""

    # 单词模式：音素50% + 重音25% + 节奏25%
    WORD_WEIGHTS = {"音素准确度": 0.50, "重音位置": 0.25, "节奏感": 0.25}

    # 句子模式：音素40% + 重音15% + 连读15% + 语调15% + 节奏15%
    SENTENCE_WEIGHTS = {
        "音素准确度": 0.40, "重音位置": 0.15,
        "连读表现": 0.15, "语调曲线": 0.15, "节奏感": 0.15,
    }

    def test_word_weights_sum(self):
        """单词模式权重和 = 1.0"""
        assert abs(sum(self.WORD_WEIGHTS.values()) - 1.0) < 1e-9

    def test_sentence_weights_sum(self):
        """句子模式权重和 = 1.0"""
        assert abs(sum(self.SENTENCE_WEIGHTS.values()) - 1.0) < 1e-9

    def test_word_mode_calculation(self):
        """单词模式综合分计算"""
        scores = {"音素准确度": 80, "重音位置": 70, "节奏感": 90}
        overall = sum(scores[k] * v for k, v in self.WORD_WEIGHTS.items())
        # 80*0.5 + 70*0.25 + 90*0.25 = 40 + 17.5 + 22.5 = 80
        assert overall == 80.0

    def test_sentence_mode_calculation(self):
        """句子模式综合分计算"""
        scores = {
            "音素准确度": 80, "重音位置": 70,
            "连读表现": 60, "语调曲线": 75, "节奏感": 85,
        }
        overall = sum(scores[k] * v for k, v in self.SENTENCE_WEIGHTS.items())
        # 80*0.4 + 70*0.15 + 60*0.15 + 75*0.15 + 85*0.15
        # = 32 + 10.5 + 9 + 11.25 + 12.75 = 75.5
        assert overall == 75.5


# ============================================================
# 音素纠错建议
# ============================================================

class TestPhonemeTips:
    """常见音素纠错建议完整性"""

    def test_common_phonemes_covered(self):
        """常见英语音素都有纠错建议"""
        common = ["TH", "R", "L", "V", "W", "S", "Z", "SH", "CH"]
        for p in common:
            assert p in PHONEME_TIPS, f"缺少音素 {p} 的纠错建议"
            assert len(PHONEME_TIPS[p]) > 5, f"音素 {p} 的建议过短"

    def test_tip_count(self):
        """至少 20 个音素有建议"""
        assert len(PHONEME_TIPS) >= 20

    def test_tips_are_chinese(self):
        """纠错建议为中文"""
        for phoneme, tip in list(PHONEME_TIPS.items())[:5]:
            assert any('\u4e00' <= c <= '\u9fff' for c in tip), f"{phoneme} 的建议不是中文"


# ============================================================
# ContentItem / RecordItem Schema
# ============================================================

class TestContentItemSchema:
    """ContentItem 字段验证"""

    def test_valid(self):
        item = ContentItem(
            id=1, title="Hello", content_text="Hello world",
            content_type="word", cefr_level="A1",
            category="日常", phonetic_ipa="həˈloʊ",
        )
        assert item.id == 1
        assert item.cefr_level == "A1"


class TestRecordItemSchema:
    """RecordItem 字段验证"""

    def test_valid(self):
        item = RecordItem(
            id=1, content_id=1, mode="word",
            overall_score=85.5, phoneme_score=80.0, stress_score=75.0,
        )
        assert item.overall_score == 85.5
        assert item.phoneme_score == 80.0
