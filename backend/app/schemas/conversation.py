"""语音对话 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConversationStartRequest(BaseModel):
    scene: str = Field(default="self_intro", description="场景标识: self_intro/directions/shopping/restaurant/hotel/airport/hospital/school")
    cefr_level: str = Field(default="B1", description="CEFR 等级: A1/A2/B1/B2")


class ConversationStartResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    ai_text: str = Field(..., description="AI 开场白文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")


class ConversationSpeakRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    scene: str = Field(default="self_intro", description="场景标识")


class ConversationSpeakResponse(BaseModel):
    user_text: str = Field(..., description="用户语音转写文本")
    ai_text: str = Field(..., description="AI 回复文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")
    grammar_correction: Optional[Dict[str, str]] = Field(
        default=None, description="语法纠错: {original, correction, tip}"
    )
    conversation_complete: bool = Field(default=False, description="对话是否结束")


class ConversationEndResponse(BaseModel):
    overall: float = Field(..., description="综合评分 (0-100)")
    pronunciation: List[Dict[str, Any]] = Field(default_factory=list, description="语音维度（wav2vec2五维均分）")
    text_dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="文本维度（LLM三维均分，简化版）")
    suggestions: str = Field(default="", description="综合改进建议")

    # 丰富数据（v2 新增）
    utterances: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="每句话的完整发音评分结果（含 viz 可视化数据）",
    )
    transcript: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="对话完整记录 [{\"role\": \"user\"|\"ai\"|\"grammar\", \"text\": \"...\"}]",
    )
    text_dimension_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="文本维度含详细评语 [{\"label\", \"score\", \"feedback\", \"strengths\", \"weaknesses\"}]",
    )
    scoring_methodology: str = Field(
        default="",
        description="综合分计算方式说明",
    )

    # 流利度评估（SRS 3.3.3）
    fluency: Optional[Dict[str, Any]] = Field(
        default=None,
        description="流利度评估报告（五维：语速/停顿/重复/语法/相关性）",
    )