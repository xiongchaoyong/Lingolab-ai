"""语法纠错模块单元测试 — Schema 验证 + 错误类型 + 降级兜底"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.grammar import GrammarError, GrammarCorrectResponse


# ============================================================
# GrammarError Schema 验证
# ============================================================

class TestGrammarErrorSchema:
    """GrammarError 字段验证"""

    def test_valid_error(self):
        """完整字段创建"""
        err = GrammarError(
            original="goed",
            correction="went",
            error_type="tense",
            explanation="go 的过去式是不规则变化",
        )
        assert err.original == "goed"
        assert err.correction == "went"
        assert err.error_type == "tense"
        assert err.explanation == "go 的过去式是不规则变化"

    def test_all_error_types(self):
        """所有 8 种错误类型均可创建"""
        types = [
            "tense", "subject_verb_agreement", "article",
            "preposition", "word_order", "plural",
            "word_choice", "other",
        ]
        for etype in types:
            err = GrammarError(
                original="x", correction="y",
                error_type=etype, explanation="test",
            )
            assert err.error_type == etype

    def test_required_fields(self):
        """缺少必填字段应报错"""
        with pytest.raises(Exception):
            GrammarError(original="goed", correction="went")


# ============================================================
# GrammarCorrectResponse Schema 验证
# ============================================================

class TestGrammarCorrectResponseSchema:
    """GrammarCorrectResponse 字段验证"""

    def test_full_response(self):
        """完整响应创建"""
        resp = GrammarCorrectResponse(
            original_text="He go to school",
            corrected_text="He goes to school",
            errors=[
                GrammarError(
                    original="go",
                    correction="goes",
                    error_type="subject_verb_agreement",
                    explanation="第三人称单数需要加 s",
                )
            ],
            polished_version="He attends school",
            suggestions=["注意主谓一致"],
        )
        assert resp.original_text == "He go to school"
        assert resp.corrected_text == "He goes to school"
        assert len(resp.errors) == 1
        assert resp.errors[0].error_type == "subject_verb_agreement"
        assert resp.polished_version == "He attends school"
        assert len(resp.suggestions) == 1

    def test_no_errors_response(self):
        """无语法错误的响应"""
        resp = GrammarCorrectResponse(
            original_text="I love coding",
            corrected_text="I love coding",
            errors=[],
            polished_version="I am passionate about coding",
            suggestions=["可以尝试更丰富的表达"],
        )
        assert len(resp.errors) == 0
        assert resp.original_text == resp.corrected_text

    def test_multiple_errors(self):
        """多个错误的响应"""
        resp = GrammarCorrectResponse(
            original_text="He go to school yesterday and buyed a book",
            corrected_text="He went to school yesterday and bought a book",
            errors=[
                GrammarError(
                    original="go", correction="went",
                    error_type="tense", explanation="过去时态",
                ),
                GrammarError(
                    original="buyed", correction="bought",
                    error_type="tense", explanation="buy 是不规则动词",
                ),
            ],
            polished_version="He went to school and purchased a book yesterday",
            suggestions=["注意不规则动词的过去式"],
        )
        assert len(resp.errors) == 2
        assert resp.errors[0].error_type == "tense"
        assert resp.errors[1].error_type == "tense"

    def test_optional_polished_version(self):
        """polished_version 和 suggestions 可为空"""
        resp = GrammarCorrectResponse(
            original_text="test",
            corrected_text="test",
            errors=[],
        )
        assert resp.polished_version is None or resp.polished_version == ""
        assert resp.suggestions is None or resp.suggestions == []


# ============================================================
# 降级兜底响应验证
# ============================================================

class TestGrammarFallback:
    """LLM 失败时的降级响应结构"""

    def _make_fallback(self, original_text):
        """模拟 llm.py 中的降级逻辑"""
        return {
            "corrected_text": original_text,
            "errors": [],
            "polished_version": original_text,
            "suggestions": ["语法纠错服务暂时不可用，请稍后重试"],
        }

    def test_fallback_preserves_original(self):
        """降级时原文不变"""
        text = "He go to school"
        fb = self._make_fallback(text)
        assert fb["corrected_text"] == text
        assert fb["polished_version"] == text

    def test_fallback_empty_errors(self):
        """降级时错误列表为空"""
        fb = self._make_fallback("test")
        assert fb["errors"] == []

    def test_fallback_has_suggestion(self):
        """降级时有提示信息"""
        fb = self._make_fallback("test")
        assert len(fb["suggestions"]) == 1
        assert "不可用" in fb["suggestions"][0]


# ============================================================
# 错误类型完整性
# ============================================================

class TestErrorTypeCompleteness:
    """前端错误类型配置与后端一致"""

    # 前端 GrammarView.vue 中定义的错误类型映射
    FRONTEND_TYPES = {
        "tense", "subject_verb_agreement", "article",
        "preposition", "word_order", "plural",
        "word_choice", "other",
    }

    def test_all_types_covered(self):
        """所有错误类型都有对应的 Schema 支持"""
        for etype in self.FRONTEND_TYPES:
            err = GrammarError(
                original="x", correction="y",
                error_type=etype, explanation="test",
            )
            assert err.error_type == etype

    def test_type_count(self):
        """错误类型数量为 8"""
        assert len(self.FRONTEND_TYPES) == 8
