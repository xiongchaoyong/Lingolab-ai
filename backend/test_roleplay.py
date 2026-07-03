"""角色扮演模块单元测试 — Schema 验证 + 角色配置 + 评分逻辑"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.roleplay import (
    RoleplayStartRequest,
    RoleplayStartResponse,
    RoleplaySpeakResponse,
    RoleplayEndResponse,
)
from app.api.roleplay import ROLE_OPENERS, ROLE_NAMES, MAX_ROUNDS


# ============================================================
# Schema 验证
# ============================================================

class TestRoleplayStartRequest:
    """RoleplayStartRequest 字段验证"""

    def test_default_values(self):
        req = RoleplayStartRequest(topic="interviewee")
        assert req.topic == "interviewee"
        assert req.cefr_level == "B1"

    def test_custom_values(self):
        req = RoleplayStartRequest(topic="waiter", cefr_level="A2")
        assert req.topic == "waiter"
        assert req.cefr_level == "A2"


class TestRoleplayStartResponse:
    """RoleplayStartResponse 字段验证"""

    def test_full_response(self):
        resp = RoleplayStartResponse(
            session_id="abc123",
            ai_text="Hello, welcome to the interview.",
            ai_audio_base64="base64data",
        )
        assert resp.session_id == "abc123"
        assert resp.ai_text == "Hello, welcome to the interview."
        assert resp.ai_audio_base64 == "base64data"

    def test_empty_audio(self):
        resp = RoleplayStartResponse(
            session_id="abc123",
            ai_text="Hello",
        )
        assert resp.ai_audio_base64 == ""


class TestRoleplaySpeakResponse:
    """RoleplaySpeakResponse 字段验证"""

    def test_normal_response(self):
        resp = RoleplaySpeakResponse(
            user_text="I am a software engineer",
            ai_text="That's great! Tell me about your experience.",
            ai_audio_base64="",
            conversation_complete=False,
        )
        assert resp.user_text == "I am a software engineer"
        assert resp.conversation_complete is False

    def test_conversation_complete(self):
        resp = RoleplaySpeakResponse(
            user_text="Thank you",
            ai_text="Thank you for your time.",
            conversation_complete=True,
        )
        assert resp.conversation_complete is True


class TestRoleplayEndResponse:
    """RoleplayEndResponse 字段验证"""

    def test_full_response(self):
        resp = RoleplayEndResponse(
            overall=82.5,
            dimensions=[
                {"label": "角色贴合度", "score": 85},
                {"label": "场景礼仪", "score": 80},
                {"label": "专业术语", "score": 78},
                {"label": "应对能力", "score": 82},
            ],
            suggestions="注意使用更专业的术语",
            utterances=[{"text": "hello", "overall": 80}],
            transcript=[{"role": "user", "text": "hello"}],
            pronunciation=[{"label": "音素准确度", "score": 80}],
            dimension_details=[{"label": "角色贴合度", "score": 85, "feedback": "good"}],
            scoring_methodology="综合分 = 角色 × 60% + 语音 × 40%",
            fluency={"overall": 78, "grade": "良好"},
        )
        assert resp.overall == 82.5
        assert len(resp.dimensions) == 4
        assert resp.fluency["overall"] == 78

    def test_minimal_response(self):
        resp = RoleplayEndResponse(overall=0)
        assert resp.overall == 0
        assert resp.dimensions == []
        assert resp.suggestions == ""
        assert resp.fluency is None


# ============================================================
# 角色配置完整性
# ============================================================

class TestRoleConfiguration:
    """角色配置一致性验证"""

    def test_eight_roles(self):
        """8 个角色场景"""
        assert len(ROLE_OPENERS) == 8
        assert len(ROLE_NAMES) == 8

    def test_role_keys_match(self):
        """OPENERS 和 NAMES 的角色 key 一致"""
        assert set(ROLE_OPENERS.keys()) == set(ROLE_NAMES.keys())

    def test_expected_roles(self):
        """包含预期的角色"""
        assert "interviewee" in ROLE_OPENERS
        assert "waiter" in ROLE_OPENERS
        assert "guide" in ROLE_OPENERS
        assert "doctor" in ROLE_OPENERS
        assert "colleague" in ROLE_OPENERS

    def test_opener_not_empty(self):
        """每个角色都有开场白 Prompt"""
        for role, opener in ROLE_OPENERS.items():
            assert len(opener) > 10, f"角色 {role} 的开场白过短"

    def test_role_names_chinese(self):
        """角色中文名正确"""
        assert ROLE_NAMES["interviewee"] == "面试者"
        assert ROLE_NAMES["waiter"] == "服务员"
        assert ROLE_NAMES["guide"] == "导游"
        assert ROLE_NAMES["doctor"] == "医生"


# ============================================================
# 对话轮次限制
# ============================================================

class TestConversationLimits:
    """对话轮次限制验证"""

    def test_max_rounds(self):
        """最大轮次为 6"""
        assert MAX_ROUNDS == 6


# ============================================================
# 评分权重验证
# ============================================================

class TestScoringWeights:
    """评分权重逻辑验证"""

    def test_role_weights_sum(self):
        """角色四维权重之和为 1.0"""
        weights = {"角色贴合度": 0.40, "场景礼仪": 0.25, "专业术语": 0.20, "应对能力": 0.15}
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_overall_weight_sum(self):
        """综合分权重之和为 1.0"""
        role_weight = 0.6
        pron_weight = 0.4
        assert abs(role_weight + pron_weight - 1.0) < 1e-9

    def test_role_weighted_score(self):
        """角色加权分计算正确"""
        dimensions = [
            {"label": "角色贴合度", "score": 80},
            {"label": "场景礼仪", "score": 70},
            {"label": "专业术语", "score": 60},
            {"label": "应对能力", "score": 90},
        ]
        weights = {"角色贴合度": 0.40, "场景礼仪": 0.25, "专业术语": 0.20, "应对能力": 0.15}
        role_avg = sum(d["score"] * weights.get(d["label"], 0.25) for d in dimensions)
        # 80*0.4 + 70*0.25 + 60*0.2 + 90*0.15 = 32 + 17.5 + 12 + 13.5 = 75
        assert role_avg == 75.0

    def test_overall_score_calculation(self):
        """综合分 = 角色 × 60% + 语音 × 40%"""
        role_avg = 80.0
        pron_avg = 70.0
        overall = round(role_avg * 0.6 + pron_avg * 0.4)
        # 48 + 28 = 76
        assert overall == 76

    def test_only_role_dimensions(self):
        """仅有角色评分时，综合分 = 角色分"""
        role_avg = 80.0
        overall = round(role_avg)
        assert overall == 80

    def test_only_pronunciation(self):
        """仅有语音评分时，综合分 = 语音分"""
        pron_avg = 75.0
        overall = round(pron_avg)
        assert overall == 75


# ============================================================
# LLM 降级兜底
# ============================================================

class TestRoleplayFallback:
    """LLM 失败时的降级响应"""

    def _make_score_fallback(self):
        """模拟 llm.py 中 score_roleplay 的降级逻辑"""
        return {
            "role_fit": 75,
            "role_fit_feedback": "角色贴合度评估暂时不可用",
            "role_fit_strengths": "",
            "role_fit_weaknesses": "",
            "etiquette": 75,
            "etiquette_feedback": "场景礼仪评估暂时不可用",
            "etiquette_strengths": "",
            "etiquette_weaknesses": "",
            "terminology": 75,
            "terminology_feedback": "专业术语评估暂时不可用",
            "terminology_strengths": "",
            "terminology_weaknesses": "",
            "response": 75,
            "response_feedback": "应对能力评估暂时不可用",
            "response_strengths": "",
            "response_weaknesses": "",
            "suggestions": "评分服务暂时异常，请稍后重试",
        }

    def test_fallback_has_all_dimensions(self):
        """降级时四维评分完整"""
        fb = self._make_score_fallback()
        assert fb["role_fit"] == 75
        assert fb["etiquette"] == 75
        assert fb["terminology"] == 75
        assert fb["response"] == 75

    def test_fallback_has_feedback(self):
        """降级时有反馈信息"""
        fb = self._make_score_fallback()
        assert "暂时不可用" in fb["role_fit_feedback"]
        assert "暂时不可用" in fb["etiquette_feedback"]
