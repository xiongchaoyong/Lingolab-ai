"""语音对话（自由对话 + 角色扮演）— 统一请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VoiceChatStartRequest(BaseModel):
    topic: str = Field(..., description="场景标识(scene模式)或角色标识(role模式)")
    mode: str = Field(default="scene", description="对话模式: scene(自由对话) | role(角色扮演)")
    cefr_level: str = Field(default="B1", description="CEFR 等级: A1/A2/B1/B2")


class VoiceChatStartResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    ai_text: str = Field(..., description="AI 开场白文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")
    mode: str = Field(default="scene", description="对话模式")
    max_rounds: int = Field(default=10, description="最大对话轮数")


class VoiceChatSpeakResponse(BaseModel):
    user_text: str = Field(..., description="用户语音转写文本")
    ai_text: str = Field(..., description="AI 回复文本")
    ai_audio_base64: str = Field(default="", description="AI 语音 MP3 (base64)")
    grammar_correction: Optional[Dict[str, Any]] = Field(default=None, description="语法纠错结果")
    conversation_complete: bool = Field(default=False, description="对话是否结束")


class VoiceChatEndResponse(BaseModel):
    overall: float = Field(..., description="综合评分 (0-100)")
    mode: str = Field(default="scene", description="对话模式")
    # === scene 模式维度 ===
    text_dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="文本维度（LLM三维均分，scene模式）")
    text_dimension_details: List[Dict[str, Any]] = Field(default_factory=list, description="文本维度含详细评语（scene模式）")
    # === role 模式维度 ===
    dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="角色扮演四维评分（role模式）")
    dimension_details: List[Dict[str, Any]] = Field(default_factory=list, description="四维评分含详细评语（role模式）")
    # === 共享字段 ===
    pronunciation: List[Dict[str, Any]] = Field(default_factory=list, description="发音维度评分（wav2vec2）")
    suggestions: str = Field(default="", description="综合改进建议")
    utterances: List[Dict[str, Any]] = Field(default_factory=list, description="每句话的完整发音评分结果")
    transcript: List[Dict[str, Any]] = Field(default_factory=list, description="对话完整记录")
    scoring_methodology: str = Field(default="", description="综合分计算方式说明")
    fluency: Optional[Dict[str, Any]] = Field(default=None, description="流利度评估报告")
