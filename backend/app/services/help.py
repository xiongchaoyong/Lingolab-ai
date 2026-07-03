"""智能客服服务 — LLM 驱动 + RAG 知识库检索 + 知识图谱推荐"""

import json
import logging
from typing import Dict, AsyncIterator

import httpx
from app.services.llm import get_llm_service, BAILIAN_API_URL
from app.services.knowledge_graph import kg_service

logger = logging.getLogger(__name__)

HELP_SYSTEM_PROMPT = """你是「Lingolab」英语学习平台的智能客服助手，名字叫"小语"。你的职责是：
1. 热情友好地回答用户关于英语学习和产品使用的任何问题
2. 回答简洁明了，一般不超过3-5句话
3. 如果遇到技术问题，给出简单排查建议
4. 如果遇到需要人工处理的问题（如退款、账号等），请用户发送邮件至 support@lingolab.com
5. 你可以和用户进行友好的对话，不仅限于产品问题

重要规则：
- 如果下方提供了「参考资料」，请优先根据参考资料中的信息回答，不要编造虚假信息
- 如果下方提供了「知识图谱推荐」，请结合图谱中的学习资源（前置技能、教学资料、相似技能）给用户具体的学习建议
- 如果参考资料不足以回答问题，请诚实告知用户，并结合你的知识给出一般性建议
- 引用参考资料时用自己的话转述，不要直接复制原文"""


class HelpService:
    """智能客服服务（RAG + 知识图谱增强版）"""

    @staticmethod
    def _rag():
        """懒加载 RAG 服务 — 避免模块导入时触发 torch 加载"""
        from app.services.rag_service import rag_service
        return rag_service

    async def chat(self, message: str, history: list, user_id: int = None) -> Dict:
        """处理用户消息：知识图谱 → RAG 检索 → LLM 生成回复"""
        try:
            # 1. 提取薄弱知识点 → 查询知识图谱
            kg_context = await self._extract_and_query_kg(message, history)

            # 2. RAG 检索
            retrieved = self._rag().search(message, top_k=3)
            rag_context = self._build_rag_context(retrieved)

            # 3. 合并上下文
            context = self._merge_context(rag_context, kg_context)

            # 4. LLM 生成
            reply = await self._ask_llm(message, history, context)

            # 5. 记录检索日志
            self._log_search(user_id, message, retrieved, reply)

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

    async def chat_stream(self, message: str, history: list, user_id: int = None) -> AsyncIterator[str]:
        """流式生成客服回复（SSE 逐 token 返回）"""
        # 1. 提取薄弱知识点 → 查询知识图谱
        kg_context = await self._extract_and_query_kg(message, history)

        # 2. RAG 检索
        retrieved = self._rag().search(message, top_k=3)
        rag_context = self._build_rag_context(retrieved)

        # 3. 合并上下文
        context = self._merge_context(rag_context, kg_context)

        # 4. 构建消息 + 流式生成
        messages = self._build_messages(message, history, context)
        llm = get_llm_service()
        full_reply = ""

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
                                    full_reply += content
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"客服流式 LLM 调用失败: {e}")
            yield "抱歉，我暂时无法处理你的问题。请稍后重试。"

        # 5. 记录检索日志
        self._log_search(user_id, message, retrieved, full_reply or None)

    # ============================================================
    # 知识图谱集成
    # ============================================================

    async def _extract_and_query_kg(self, message: str, history: list) -> str:
        """提取用户薄弱知识点 → 查询知识图谱 → 返回结构化上下文"""
        try:
            weakness = await self._extract_weakness(message, history)
            if not weakness:
                return ""

            logger.info(f"客服提取薄弱点: {weakness}")
            result = kg_service.find_recommendations(weakness)
            if not result["found"]:
                return ""

            return self._build_kg_context(result)
        except Exception as e:
            logger.warning(f"知识图谱查询失败: {e}")
            return ""

    async def _extract_weakness(self, message: str, history: list) -> str:
        """轻量级 LLM 调用：从用户问题中提取薄弱知识点

        返回: "过去时" / "th发音" / "虚拟语气" / "" (无薄弱点)
        """
        llm = get_llm_service()

        # 构建提取 prompt（非常精简，只需返回关键词）
        extract_messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识点提取器。从用户的问题中提取他们提到的薄弱知识点（语法、发音、词汇等）。"
                    "只返回知识点名称（中文优先，不超过8个字），不要任何解释或标点。"
                    "如果用户没有提到任何薄弱知识点，只返回一个字：无"
                ),
            },
            {"role": "user", "content": message},
        ]

        try:
            result = await llm._raw_chat_messages(extract_messages, temperature=0.1, max_tokens=20)
            result = result.strip().rstrip("。，！？,.!?")
            if not result or result == "无" or len(result) > 20:
                return ""
            logger.info(f"LLM 提取知识点: '{result}'")
            return result
        except Exception as e:
            logger.warning(f"知识点提取失败: {e}")
            return ""

    def _build_kg_context(self, result: dict) -> str:
        """将知识图谱查询结果格式化为 LLM prompt 上下文"""
        keyword = result.get("keyword", "")
        lines = [f"知识图谱推荐（关键词：{keyword}）："]

        for i, item in enumerate(result.get("results", [])[:3], 1):
            skill = item.get("skill", {})
            skill_label = skill.get("label", skill.get("id", "未知技能"))

            lines.append(f"\n{i}. 【{skill_label}】")
            if item.get("cefr_level") and item["cefr_level"] != "未知":
                lines.append(f"   CEFR 等级：{item['cefr_level']}")

            prereqs = item.get("prerequisites", [])
            if prereqs:
                names = " → ".join(p["label"] for p in prereqs)
                lines.append(f"   前置技能：{names}")

            materials = item.get("materials", [])
            if materials:
                names = "、".join(m["label"] for m in materials[:5])
                lines.append(f"   推荐资料：{names}")

            similar = item.get("similar_skills", [])
            if similar:
                names = "、".join(s["label"] for s in similar)
                lines.append(f"   易混淆技能：{names}")

        return "\n".join(lines)

    def _merge_context(self, rag_context: str, kg_context: str) -> str:
        """合并 RAG 和 KG 上下文"""
        parts = []
        if kg_context:
            parts.append(kg_context)
        if rag_context:
            parts.append(rag_context)
        return "\n\n".join(parts)

    # ============================================================
    # LLM 调用
    # ============================================================

    async def _ask_llm(self, message: str, history: list, context: str) -> str:
        """调用 LLM 生成客服回复"""
        messages = self._build_messages(message, history, context)
        llm = get_llm_service()
        return await llm._raw_chat_messages(messages, temperature=0.7, max_tokens=300)

    def _build_messages(self, message: str, history: list, context: str = "") -> list:
        """构建 LLM 消息列表"""
        system_content = HELP_SYSTEM_PROMPT
        if context:
            system_content += f"\n\n{context}"

        messages = [{"role": "system", "content": system_content}]

        for h in history[-10:]:
            if h.get("role") == "user":
                messages.append({"role": "user", "content": h.get("text", "")})
            elif h.get("role") == "ai":
                messages.append({"role": "assistant", "content": h.get("text", "")})

        messages.append({"role": "user", "content": message})
        return messages

    # ============================================================
    # RAG 上下文
    # ============================================================

    def _build_rag_context(self, retrieved: list) -> str:
        """将检索到的文档结构化为 prompt 上下文"""
        if not retrieved:
            return ""
        lines = ["参考资料："]
        for i, doc in enumerate(retrieved, 1):
            title = doc["metadata"].get("title", f"文档{doc['id']}") if doc["metadata"] else f"文档{doc['id']}"
            lines.append(f"{i}. 【{title}】{doc['text'][:300]}")
        return "\n".join(lines)

    # ============================================================
    # 检索日志
    # ============================================================

    def _log_search(self, user_id, query, retrieved, reply):
        """异步记录检索日志（fire-and-forget）"""
        try:
            from app.core.database import SessionLocal
            from app.models.knowledge_base import SearchLog

            db = SessionLocal()
            docs_info = [
                {"id": r["id"], "title": r["metadata"].get("title", "") if r["metadata"] else "", "score": r["score"]}
                for r in retrieved
            ]
            reply_snippet = reply[:200] if reply else None
            db.add(SearchLog(
                user_id=user_id,
                query=query,
                retrieved_docs=docs_info,
                reply=reply_snippet,
            ))
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"记录检索日志失败: {e}")


help_service = HelpService()
