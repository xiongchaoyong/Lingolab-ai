"""智能客服 Schema"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """文字客服请求"""
    message: str = Field(..., min_length=1, max_length=500)
    history: List[dict] = Field(default_factory=list)  # [{"role":"user/ai","text":"..."}]


class ChatResponse(BaseModel):
    """客服回复"""
    reply: str
    category: str = "study_advice"  # product_use/study_advice/tech_issue/refund/off_topic
    escalate: bool = False  # 是否建议转人工
    transcript: Optional[str] = None  # 语音输入时的 ASR 转写文本


class FaqItem(BaseModel):
    """FAQ 条目"""
    q: str
    a: str


class FaqCategory(BaseModel):
    """FAQ 分类"""
    title: str
    icon: str
    questions: List[FaqItem] = Field(default_factory=list)