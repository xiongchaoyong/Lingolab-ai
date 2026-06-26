"""服务模块7（客服服务）单元测试 — Schema 验证 + 重复检测 + 常量完整性"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.help import ChatRequest, ChatResponse, FaqItem, FaqCategory
from app.services.help import HelpService, OUT_OF_SCOPE_REPLIES, HELP_SYSTEM_PROMPT


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
# 重复检测
# ============================================================

class TestRepeatDetection:
    """重复问题检测"""

    def setup_method(self):
        self.service = HelpService()

    def test_no_repeat_short_history(self):
        """少于3条消息不算重复"""
        history = [{"role": "user", "text": "你好"}]
        assert self.service._check_repeat("你好", history) is False

    def test_no_repeat_empty(self):
        """空历史不算重复"""
        assert self.service._check_repeat("你好", []) is False

    def test_repeat_identical_3_times(self):
        """连续3条相同消息算重复"""
        history = [
            {"role": "user", "text": "怎么退款"},
            {"role": "ai", "text": "请联系客服"},
            {"role": "user", "text": "怎么退款"},
            {"role": "ai", "text": "请联系客服"},
        ]
        assert self.service._check_repeat("怎么退款", history) is True

    def test_no_repeat_different_messages(self):
        """3条不同消息不算重复"""
        history = [
            {"role": "user", "text": "你好"},
            {"role": "ai", "text": "你好！"},
            {"role": "user", "text": "怎么注册"},
            {"role": "ai", "text": "点击注册"},
        ]
        assert self.service._check_repeat("发音评测怎么用", history) is False

    def test_repeat_similar_prefix(self):
        """最近3条用户消息以相同前缀(前10字符)开头算重复"""
        # _check_repeat 逻辑：last3[0][:10] in m for m in last3[1:]
        # last3 = recent_user_msgs[-3:] = [倒数第3, 倒数第2, 当前]
        # last3[0] 是倒数第3条用户消息，取其前10字符检查是否在后2条中出现
        history = [
            {"role": "user", "text": "请问怎么退款呢拜托了啊啊"},
            {"role": "ai", "text": "请联系客服"},
            {"role": "user", "text": "请问怎么退款呢拜托了我想退"},
            {"role": "ai", "text": "请联系客服"},
        ]
        # last3[0] = "请问怎么退款呢拜托了我想退"[:10] = "请问怎么退款呢拜托"
        # 检查 "请问怎么退款呢拜托" in last3[1] 和 in current
        assert self.service._check_repeat("请问怎么退款呢拜托了拜托", history) is True


# ============================================================
# 常量完整性
# ============================================================

class TestConstants:
    """常量和配置完整性"""

    def test_out_of_scope_keys(self):
        """超范围回复覆盖3种类别"""
        expected = {"tech_issue", "refund", "off_topic"}
        assert set(OUT_OF_SCOPE_REPLIES.keys()) == expected

    def test_out_of_scope_non_empty(self):
        """每条固定回复非空"""
        for key, reply in OUT_OF_SCOPE_REPLIES.items():
            assert len(reply) > 10, f"{key} 回复太短"

    def test_help_system_prompt_contains_platform_info(self):
        """系统 Prompt 包含平台信息"""
        assert "Lingolab" in HELP_SYSTEM_PROMPT
        assert "发音评测" in HELP_SYSTEM_PROMPT
        assert "学习路径" in HELP_SYSTEM_PROMPT
        assert "角色扮演" in HELP_SYSTEM_PROMPT

    def test_help_system_prompt_contains_constraints(self):
        """系统 Prompt 包含行为约束"""
        assert "support@lingolab.com" in HELP_SYSTEM_PROMPT
        assert "3句话" in HELP_SYSTEM_PROMPT or "不超过" in HELP_SYSTEM_PROMPT
