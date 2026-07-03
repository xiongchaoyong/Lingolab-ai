"""服务模块7（客服服务）单元测试 — Schema 验证 + 常量完整性"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.help import ChatRequest, ChatResponse, FaqItem, FaqCategory
from app.services.help import HelpService, HELP_SYSTEM_PROMPT


# ============================================================
# Schema 验证
# ============================================================

class TestChatSchemas:
    """客服 Schema 验证"""

    def test_chat_request(self):
        req = ChatRequest(message="如何练习发音？")
        assert req.message == "如何练习发音？"
        assert req.history == []

    def test_chat_request_with_history(self):
        req = ChatRequest(
            message="继续",
            history=[{"role": "user", "text": "你好"}, {"role": "ai", "text": "你好！"}],
        )
        assert len(req.history) == 2

    def test_chat_request_empty_message(self):
        """消息不能为空"""
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_chat_request_long_message(self):
        """消息最长 500 字符"""
        with pytest.raises(Exception):
            ChatRequest(message="x" * 501)

    def test_chat_response(self):
        resp = ChatResponse(reply="你好！", category="study_advice", escalate=False)
        assert resp.reply == "你好！"
        assert resp.escalate is False

    def test_chat_response_with_transcript(self):
        resp = ChatResponse(reply="你好", category="product_use", transcript="你好")
        assert resp.transcript == "你好"

    def test_chat_response_defaults(self):
        resp = ChatResponse(reply="test")
        assert resp.category == "study_advice"
        assert resp.escalate is False
        assert resp.transcript is None


# ============================================================
# FAQ Schema
# ============================================================

class TestFaqSchemas:
    """FAQ Schema 验证"""

    def test_faq_item(self):
        item = FaqItem(q="如何注册？", a="点击注册按钮")
        assert item.q == "如何注册？"
        assert item.a == "点击注册按钮"

    def test_faq_category(self):
        cat = FaqCategory(title="账号相关", icon="User", questions=[
            FaqItem(q="如何注册？", a="点击注册"),
        ])
        assert cat.title == "账号相关"
        assert len(cat.questions) == 1

    def test_faq_category_empty_questions(self):
        cat = FaqCategory(title="测试", icon="Test")
        assert cat.questions == []


# ============================================================
# 常量完整性
# ============================================================

class TestConstants:
    """常量和配置完整性"""

    def test_help_system_prompt_contains_platform_info(self):
        """系统 Prompt 包含平台信息"""
        assert "Lingolab" in HELP_SYSTEM_PROMPT
        assert "小语" in HELP_SYSTEM_PROMPT
        assert "英语学习" in HELP_SYSTEM_PROMPT

    def test_help_system_prompt_contains_constraints(self):
        """系统 Prompt 包含行为约束"""
        assert "support@lingolab.com" in HELP_SYSTEM_PROMPT
        assert "3-5句话" in HELP_SYSTEM_PROMPT or "不超过" in HELP_SYSTEM_PROMPT

    def test_help_system_prompt_has_rag_rules(self):
        """系统 Prompt 包含 RAG + 知识图谱规则"""
        assert "参考资料" in HELP_SYSTEM_PROMPT
        assert "知识图谱" in HELP_SYSTEM_PROMPT
