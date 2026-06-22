"""LLM 对话服务 — 阿里百炼 DashScope API 封装"""

import json
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BAILIAN_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen-plus"

# 场景 Prompt 模板
SCENE_PROMPTS = {
    "self_intro": (
        "You are Alex, a friendly English conversation partner. "
        "The user is practicing English self-introduction. "
        "Your role: ask questions about their name, job, hobbies, family, and interests. "
        "Keep responses short (1-3 sentences), natural, and encouraging. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
    "directions": (
        "You are a tourist in an English-speaking city. "
        "The user is a local helping you with directions. "
        "Your role: ask how to get to various places (subway, bus stop, restaurant, museum). "
        "Respond naturally to the directions given. Keep responses short (1-3 sentences). "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
    "shopping": (
        "You are a shop assistant in a clothing store. "
        "The user is a customer looking for clothes. "
        "Your role: help them find items, suggest sizes/colors, discuss prices and discounts. "
        "Keep responses short (1-3 sentences), polite and helpful. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
    "restaurant": (
        "You are a waiter/waitress in a restaurant. "
        "The user is a customer dining in. "
        "Your role: greet them, take orders, recommend dishes, answer questions about the menu. "
        "Keep responses short (1-3 sentences), professional and friendly. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
}

# 角色扮演 Prompt 模板
ROLE_PROMPTS = {
    "interviewee": (
        "You are a professional interviewer conducting a job interview in English. "
        "The user is the candidate (interviewee) applying for a position. "
        "Your role: ask realistic interview questions about self-introduction, project experience, "
        "career planning, strengths and weaknesses, and salary expectations. "
        "Respond naturally to their answers and ask follow-up questions. "
        "Keep responses short (1-3 sentences), professional and natural. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
    "waiter": (
        "You are a customer dining at a restaurant. "
        "The user is the waiter/waitress serving you. "
        "Your role: order food, ask about menu ingredients and specials, make special requests "
        "(allergies, dietary restrictions), ask for recommendations, and pay the bill. "
        "Act like a real customer — be polite but also ask questions. "
        "Keep responses short (1-3 sentences), friendly and natural. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
    "guide": (
        "You are a tourist visiting a famous attraction. "
        "The user is your tour guide showing you around. "
        "Your role: ask about the history and culture of the site, get directions to specific spots, "
        "ask for food recommendations, and inquire about local customs. "
        "Show curiosity and engagement in the tour. "
        "Keep responses short (1-3 sentences), curious and engaged. "
        "Adapt your vocabulary to the user's CEFR level ({level})."
    ),
}

# CEFR 难度对应的语言要求
CEFR_DIFFICULTY = {
    "A1": "Use very simple words and short sentences. Speak slowly with basic vocabulary.",
    "A2": "Use simple everyday vocabulary. Keep sentences short and clear.",
    "B1": "Use intermediate vocabulary. You may use some phrasal verbs and idioms.",
    "B2": "Use advanced vocabulary naturally. You may speak at normal speed with complex sentences.",
}


class LLMService:
    """阿里百炼 大语言模型对话服务"""

    def __init__(self):
        self.api_key = settings.bailian_api_key
        self.model = DEFAULT_MODEL

    async def chat(
        self,
        scene: str,
        user_text: str,
        history: list[dict],
        cefr_level: str = "B1",
    ) -> str:
        """
        生成 AI 对话回复

        Args:
            scene: 场景标识 (self_intro/directions/shopping/restaurant)
            user_text: 用户当前轮次的转写文本
            history: 对话历史 [{"role": "user", "text": "..."}, {"role": "ai", "text": "..."}]
            cefr_level: 用户 CEFR 等级

        Returns:
            AI 回复文本
        """
        system_prompt = SCENE_PROMPTS.get(scene, SCENE_PROMPTS["self_intro"])
        level_instruction = CEFR_DIFFICULTY.get(cefr_level, CEFR_DIFFICULTY["B1"])
        system_prompt = system_prompt.format(level=cefr_level) + " " + level_instruction
        system_prompt += " Vary your phrasing each time — never repeat the same opening or question. Do NOT use emojis or special symbols in your replies — plain English text only."

        messages = [{"role": "system", "content": system_prompt}]

        # 构建对话历史（最近 10 轮）
        for h in history[-10:]:
            if h["role"] == "user":
                messages.append({"role": "user", "content": h["text"]})
            elif h["role"] == "ai":
                messages.append({"role": "assistant", "content": h["text"]})

        # 当前用户输入
        messages.append({"role": "user", "content": user_text})

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.9,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                logger.info(f"LLM 回复: {reply[:80]}...")
                return reply

        except httpx.HTTPStatusError as e:
            logger.error(f"百炼 API 错误 {e.response.status_code}: {e.response.text[:200]}")
            if e.response.status_code == 401:
                return "I'm having trouble connecting right now. Please check the API configuration."
            return "Sorry, I'm having trouble thinking right now. Could you repeat that?"
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return "I didn't catch that. Could you say it again?"

    async def chat_stream(
        self,
        scene: str,
        user_text: str,
        history: list[dict],
        cefr_level: str = "B1",
    ):
        """
        流式生成 AI 对话回复（SSE 逐 token 返回）

        Yields:
            str: 增量文本片段
        """
        system_prompt = SCENE_PROMPTS.get(scene, SCENE_PROMPTS["self_intro"])
        level_instruction = CEFR_DIFFICULTY.get(cefr_level, CEFR_DIFFICULTY["B1"])
        system_prompt = system_prompt.format(level=cefr_level) + " " + level_instruction
        system_prompt += " Vary your phrasing each time — never repeat the same opening or question. Do NOT use emojis or special symbols in your replies — plain English text only."

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if h["role"] == "user":
                messages.append({"role": "user", "content": h["text"]})
            elif h["role"] == "ai":
                messages.append({"role": "assistant", "content": h["text"]})

        messages.append({"role": "user", "content": user_text})

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream(
                    "POST",
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.9,
                        "stream": True,
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

        except httpx.HTTPStatusError as e:
            logger.error(f"百炼流式 API 错误 {e.response.status_code}: {e.response.text[:200]}")
            yield "Sorry, I'm having trouble thinking right now. Could you repeat that?"
        except Exception as e:
            logger.error(f"LLM 流式调用失败: {e}")
            yield "I didn't catch that. Could you say it again?"

    async def score_conversation(self, history: list[dict], cefr_level: str = "B1") -> dict:
        """
        对话结束后评分 — 仅文本维度（语法/词汇/参与度），发音由 wav2vec2 评分

        Returns:
            {"grammar": 75, "vocabulary": 70, "engagement": 85, "suggestions": "..."}
        """
        dialogue = ""
        for h in history:
            role = "User" if h["role"] == "user" else "AI"
            dialogue += f"{role}: {h['text']}\n"

        prompt = (
            f"You are an English teacher evaluating a student's conversation practice.\n"
            f"Student CEFR level: {cefr_level}\n\n"
            f"Conversation:\n{dialogue}\n\n"
            f"Score the student on 3 text-based dimensions (0-100 each).\n"
            f"For each dimension, provide a score, a brief feedback sentence, "
            f"one strength observation, and one weakness/improvement suggestion.\n\n"
            f"1. grammar_accuracy - correct grammar usage and sentence structure\n"
            f"2. vocabulary_range - variety and appropriateness of vocabulary\n"
            f"3. engagement - active participation, relevance, and conversation flow\n\n"
            f"Return ONLY a JSON object (no markdown, no code fences):\n"
            f'{{"grammar": 75,'
            f'"grammar_feedback": "brief Chinese feedback on grammar",'
            f'"grammar_strengths": "one specific grammar strength",'
            f'"grammar_weaknesses": "one specific grammar issue to improve",'
            f'"vocabulary": 70,'
            f'"vocabulary_feedback": "brief Chinese feedback on vocabulary",'
            f'"vocabulary_strengths": "one specific vocabulary strength",'
            f'"vocabulary_weaknesses": "one specific vocabulary issue to improve",'
            f'"engagement": 85,'
            f'"engagement_feedback": "brief Chinese feedback on engagement",'
            f'"engagement_strengths": "one specific engagement strength",'
            f'"engagement_weaknesses": "one specific engagement issue to improve",'
            f'"suggestions": "overall improvement advice in Chinese"}}'
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 800,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # 清理可能的 markdown 代码块
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)

        except Exception as e:
            logger.error(f"对话评分失败: {e}")
            return {
                "grammar": 75,
                "grammar_feedback": "语法评估暂时不可用",
                "grammar_strengths": "",
                "grammar_weaknesses": "",
                "vocabulary": 75,
                "vocabulary_feedback": "词汇评估暂时不可用",
                "vocabulary_strengths": "",
                "vocabulary_weaknesses": "",
                "engagement": 75,
                "engagement_feedback": "参与度评估暂时不可用",
                "engagement_strengths": "",
                "engagement_weaknesses": "",
                "suggestions": "继续练习，多说多练！",
            }

    async def chat_roleplay(
        self,
        role: str,
        user_text: str,
        history: list[dict],
        cefr_level: str = "B1",
    ) -> str:
        """
        角色扮演 — 生成 AI 对话回复

        Args:
            role: 角色标识 (interviewee/waiter/guide)
            user_text: 用户当前轮次的转写文本
            history: 对话历史
            cefr_level: 用户 CEFR 等级

        Returns:
            AI 回复文本
        """
        system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["interviewee"])
        level_instruction = CEFR_DIFFICULTY.get(cefr_level, CEFR_DIFFICULTY["B1"])
        system_prompt = system_prompt.format(level=cefr_level) + " " + level_instruction
        system_prompt += " Vary your phrasing each time — never repeat the same opening or question. Do NOT use emojis or special symbols in your replies — plain English text only."

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if h["role"] == "user":
                messages.append({"role": "user", "content": h["text"]})
            elif h["role"] == "ai":
                messages.append({"role": "assistant", "content": h["text"]})

        messages.append({"role": "user", "content": user_text})

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.9,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                logger.info(f"角色扮演 LLM 回复: {reply[:80]}...")
                return reply

        except httpx.HTTPStatusError as e:
            logger.error(f"百炼 API 错误 {e.response.status_code}: {e.response.text[:200]}")
            return "I'm sorry, I'm having trouble connecting right now. Could you repeat that?"
        except Exception as e:
            logger.error(f"LLM 角色扮演调用失败: {e}")
            return "I didn't catch that. Could you say it again?"

    async def chat_roleplay_stream(
        self,
        role: str,
        user_text: str,
        history: list[dict],
        cefr_level: str = "B1",
    ):
        """
        角色扮演 — 流式生成 AI 回复

        Yields:
            str: 增量文本片段
        """
        system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["interviewee"])
        level_instruction = CEFR_DIFFICULTY.get(cefr_level, CEFR_DIFFICULTY["B1"])
        system_prompt = system_prompt.format(level=cefr_level) + " " + level_instruction
        system_prompt += " Vary your phrasing each time — never repeat the same opening or question. Do NOT use emojis or special symbols in your replies — plain English text only."

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if h["role"] == "user":
                messages.append({"role": "user", "content": h["text"]})
            elif h["role"] == "ai":
                messages.append({"role": "assistant", "content": h["text"]})

        messages.append({"role": "user", "content": user_text})

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream(
                    "POST",
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.9,
                        "stream": True,
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

        except httpx.HTTPStatusError as e:
            logger.error(f"百炼流式 API 错误: {e}")
            yield "I'm sorry, I'm having trouble connecting right now. Could you repeat that?"
        except Exception as e:
            logger.error(f"LLM 角色扮演流式调用失败: {e}")
            yield "I didn't catch that. Could you say it again?"

    async def score_roleplay(self, history: list[dict], cefr_level: str = "B1") -> dict:
        """
        角色扮演结束后评分 — 四维评分（角色贴合度/场景礼仪/专业术语/应对能力）

        Returns:
            {"role_fit": 80, "etiquette": 75, "terminology": 70, "response": 72,
             "suggestions": "..."}
        """
        dialogue = ""
        for h in history:
            role = "User" if h["role"] == "user" else "AI"
            dialogue += f"{role}: {h['text']}\n"

        prompt = (
            f"You are an English teacher evaluating a student's role-play performance.\n"
            f"Student CEFR level: {cefr_level}\n\n"
            f"Role-play conversation:\n{dialogue}\n\n"
            f"Score the student on 4 dimensions (0-100 each) specific to role-play scenarios.\n"
            f"For each dimension, provide a score, a brief feedback sentence in Chinese, "
            f"one strength observation, and one weakness/improvement suggestion.\n\n"
            f"1. role_fit - whether the student's expressions match their assigned role and context\n"
            f"2. etiquette - use of polite language, appropriate greetings, formality level\n"
            f"3. terminology - correct use of scenario-specific vocabulary and professional terms\n"
            f"4. response - ability to handle unexpected situations and respond appropriately\n\n"
            f"Return ONLY a JSON object (no markdown, no code fences):\n"
            f'{{"role_fit": 80,'
            f'"role_fit_feedback": "brief Chinese feedback on role fit",'
            f'"role_fit_strengths": "specific role fit strength",'
            f'"role_fit_weaknesses": "specific role fit improvement",'
            f'"etiquette": 75,'
            f'"etiquette_feedback": "brief Chinese feedback on etiquette",'
            f'"etiquette_strengths": "specific etiquette strength",'
            f'"etiquette_weaknesses": "specific etiquette improvement",'
            f'"terminology": 70,'
            f'"terminology_feedback": "brief Chinese feedback on terminology",'
            f'"terminology_strengths": "specific terminology strength",'
            f'"terminology_weaknesses": "specific terminology improvement",'
            f'"response": 72,'
            f'"response_feedback": "brief Chinese feedback on response ability",'
            f'"response_strengths": "specific response strength",'
            f'"response_weaknesses": "specific response improvement",'
            f'"suggestions": "overall improvement advice in Chinese"}}'
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    BAILIAN_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 800,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                content = content.replace("```json", "").replace("```", "").strip()
                result = json.loads(content)
                logger.info(f"角色扮演评分完成: role_fit={result.get('role_fit')}, etiquette={result.get('etiquette')}")
                return result

        except Exception as e:
            logger.error(f"角色扮演评分失败: {e}")
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
                "suggestions": "继续练习，尝试在角色中更自然地表达自己！",
            }


# 全局单例
_llm_instance = None


def get_llm_service() -> LLMService:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMService()
    return _llm_instance