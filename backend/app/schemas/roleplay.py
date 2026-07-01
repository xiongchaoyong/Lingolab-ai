"""角色扮演 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RoleplayStartRequest(BaseModel):
    role: str = Field(default="interviewee", description="角色: interviewee/waiter/guide/doctor/teacher/customer_service/receptionist/colleague")
    cefr_level: str = Field(default="B1", description="CEFR 等级: A1/A2/B1/B2")


class RoleplayStartResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    ai_text: str = Field(..., description="AI 开场白文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")


class RoleplaySpeakResponse(BaseModel):
    user_text: str = Field(..., description="用户语音转写文本")
    ai_text: str = Field(..., description="AI 回复文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")
    grammar_correction: Optional[Dict[str, Any]] = Field(
        default=None, description="语法纠错结果"
    )
    conversation_complete: bool = Field(default=False, description="对话是否结束")


class RoleplayEndResponse(BaseModel):
    overall: float = Field(..., description="综合评分 (0-100)")
    dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="角色扮演四维评分")
    suggestions: str = Field(default="", description="综合改进建议")

    # 丰富数据
    utterances: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="每句话的发音评分结果",
    )
    transcript: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="对话完整记录",
    )
    pronunciation: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="发音维度评分（wav2vec2）",
    )
    dimension_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="四维评分含详细评语",
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