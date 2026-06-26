"""智能客服服务 — LLM 驱动的自由对话"""

import json
import logging
from typing import Dict, AsyncIterator

import httpx
from app.services.llm import get_llm_service, BAILIAN_API_URL

logger = logging.getLogger(__name__)

# 客服系统 Prompt
HELP_SYSTEM_PROMPT = """你是「Lingolab」英语学习平台的智能客服助手，名字叫"小语"。你的职责是：
1. 热情友好地回答用户关于英语学习和产品使用的任何问题
2. 回答简洁明了，一般不超过3-5句话
3. 如果遇到技术问题，给出简单排查建议
4. 如果遇到需要人工处理的问题（如退款、账号等），请用户发送邮件至 support@lingolab.com
5. 你可以和用户进行友好的对话，不仅限于产品问题

关于 Lingolab 平台的信息：
- 发音评测：基于 AI 从音素准确度、重音、连读、语调、节奏五个维度评分，支持单词和句子模式
- AI 对话：支持餐厅、酒店、机场、购物等场景，AI 角色扮演对话练习
- 学习路径：根据 CEFR 等级自动生成每日跟读+对话+听力任务
- 语法纠错：AI 实时纠正语法错误并给出润色建议
- 角色扮演：支持面试者、服务员、导游等场景
- 闯关挑战：每日闯关+配音挑战+积分徽章系统
- 社区：语音挑战广场+讨论区+学习小组
- 测评：自适应难度水平测试，CEFR A1-C2 定级
- 免费版每天3次发音评测+1次AI对话，付费版不限次数"""


class HelpService:
    """智能客服服务"""

    async def chat(self, message: str, history: list) -> Dict:
        """处理用户消息，直接返回 LLM 回复"""
        try:
            reply = await self._ask_llm(message, history)
            return {
                "reply": reply,
                "category": "",
                "escalate": False,
            }
        except Exception as e:
            logger.error(f"客服 LLM 调用失败: {e}")
            return {
                "reply": "抱歉，我暂时无法处理你的问题。请稍后重试，或发送邮件至 support@lingolab.com 联系人工客服。",
                "category": "",
                "escalate": True,
            }

    async def _ask_llm(self, message: str, history: list) -> str:
        """调用 LLM 生成客服回复"""
        messages = self._build_messages(message, history)
        llm = get_llm_service()
        return await llm._raw_chat_messages(messages, temperature=0.7, max_tokens=300)

    def _build_messages(self, message: str, history: list) -> list:
        """构建 LLM 消息列表"""
        messages = [{"role": "system", "content": HELP_SYSTEM_PROMPT}]

        for h in history[-10:]:
            if h.get("role") == "user":
                messages.append({"role": "user", "content": h.get("text", "")})
            elif h.get("role") == "ai":
                messages.append({"role": "assistant", "content": h.get("text", "")})

        messages.append({"role": "user", "content": message})
        return messages

    async def chat_stream(self, message: str, history: list) -> AsyncIterator[str]:
        """流式生成客服回复（SSE 逐 token 返回）"""
        messages = self._build_messages(message, history)
        llm = get_llm_service()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream(
                    "POST",
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {llm.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": llm.model,
                        "messages": messages,
                        "max_tokens": 300,
                        "temperature": 0.7,
                        "stream": True,
                        "enable_thinking": False,
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"客服流式 LLM 调用失败: {e}")
            yield "抱歉，我暂时无法处理你的问题。请稍后重试。"


help_service = HelpService()