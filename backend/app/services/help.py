"""智能客服服务 — LLM 驱动的问题解答 + 分类 + 转人工"""

import logging
from typing import Dict

from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

# 客服系统 Prompt
HELP_SYSTEM_PROMPT = """你是一个英语学习平台「Lingolab」的智能客服助手。你的职责是：
1. 只回答与产品使用和英语学习相关的问题
2. 回答简洁友好，不超过3句话
3. 如果用户遇到技术问题（如录音无反应、页面加载失败），给出简单排查建议后建议联系人工客服
4. 如果用户询问退款、付费、账号禁用等需要人工处理的问题，礼貌说明这是智能客服无法处理的，请用户发送邮件至 support@lingolab.com
5. 如果用户闲聊或问无关问题，礼貌表示你只能回答产品使用和英语学习相关问题

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

# 超出范围的固定回复
OUT_OF_SCOPE_REPLIES = {
    "tech_issue": "这听起来像是一个技术问题。建议你尝试：① 检查浏览器麦克风权限 ② 使用 Chrome 最新版 ③ 清理缓存后重试。如果问题仍然存在，请发送邮件至 support@lingolab.com，我们的技术团队会尽快处理。",
    "refund": "退款和付费相关的问题我无法直接处理。请发送邮件至 support@lingolab.com，客服人员会在 1-2 个工作日内回复。",
    "off_topic": "抱歉，我只能回答 Lingolab 产品使用和英语学习相关的问题。请问有什么关于英语学习或平台使用的问题我可以帮你吗？",
}

# 问题分类 Prompt
CLASSIFY_PROMPT = """请对以下用户消息进行分类，只回复一个类别标签：
- product_use：产品使用方法、功能咨询
- study_advice：英语学习方法、学习建议
- tech_issue：技术故障、bug、录音问题等
- refund：退款、付费、账号相关
- off_topic：闲聊、无关话题

用户消息：{message}

类别："""


class HelpService:
    """智能客服服务"""

    async def chat(self, message: str, history: list) -> Dict:
        """处理用户消息，返回 AI 回复 + 分类 + 转人工标记"""
        # 1. 问题分类
        category = await self._classify(message)

        # 2. 超出范围 → 固定话术
        if category in OUT_OF_SCOPE_REPLIES:
            return {
                "reply": OUT_OF_SCOPE_REPLIES[category],
                "category": category,
                "escalate": True,
            }

        # 3. 检查是否连续3次相同问题 → 引导人工
        escalate = self._check_repeat(message, history)

        # 4. 调用 LLM 生成回复
        try:
            reply = await self._ask_llm(message, history, escalate)
            return {
                "reply": reply,
                "category": category,
                "escalate": escalate,
            }
        except Exception as e:
            logger.error(f"客服 LLM 调用失败: {e}")
            # 降级：返回 FAQ 提示
            return {
                "reply": "抱歉，我暂时无法处理你的问题。请尝试查看左侧的常见问题分类，或发送邮件至 support@lingolab.com 联系人工客服。",
                "category": "tech_issue",
                "escalate": True,
            }

    async def _classify(self, message: str) -> str:
        """调用 LLM 进行问题分类"""
        try:
            llm = get_llm_service()
            prompt = CLASSIFY_PROMPT.format(message=message)
            result = await llm._raw_chat(prompt, temperature=0.1, max_tokens=10)
            result = result.strip().lower()
            valid_categories = {"product_use", "study_advice", "tech_issue", "refund", "off_topic"}
            if result in valid_categories:
                return result
            return "study_advice"  # 默认归类
        except Exception as e:
            logger.warning(f"问题分类失败: {e}")
            return "study_advice"

    async def _ask_llm(self, message: str, history: list, escalate: bool) -> str:
        """调用 LLM 生成客服回复"""
        messages = [{"role": "system", "content": HELP_SYSTEM_PROMPT}]

        # 最近 6 轮对话历史
        for h in history[-6:]:
            if h.get("role") == "user":
                messages.append({"role": "user", "content": h.get("text", "")})
            elif h.get("role") == "ai":
                messages.append({"role": "assistant", "content": h.get("text", "")})

        messages.append({"role": "user", "content": message})

        if escalate:
            messages.append({"role": "user", "content": "（如果这个问题你已经回答过多次，请在回复末尾补充：如果还有疑问，可以发送邮件至 support@lingolab.com 联系人工客服）"})

        llm = get_llm_service()
        return await llm._raw_chat_messages(messages, temperature=0.7, max_tokens=200)

    def _check_repeat(self, message: str, history: list) -> bool:
        """检查是否连续3次提出相似问题"""
        recent_user_msgs = [
            h.get("text", "") for h in history[-6:]
            if h.get("role") == "user"
        ]
        recent_user_msgs.append(message)
        if len(recent_user_msgs) < 3:
            return False
        # 简易重复检测：最近3条消息完全相同或高度相似
        last3 = recent_user_msgs[-3:]
        if len(set(last3)) == 1:
            return True
        # 检查是否包含相同关键词
        if len(last3[0]) > 2 and all(last3[0][:10] in m for m in last3[1:]):
            return True
        return False


help_service = HelpService()