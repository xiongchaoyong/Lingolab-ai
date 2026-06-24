"""语法纠错 — 请求/响应 Schema"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GrammarError(BaseModel):
    """单个语法错误"""
    original: str = Field(..., description="原文中的错误部分")
    correction: str = Field(..., description="建议修正")
    error_type: str = Field(
        ...,
        description="错误类型: tense/subject_verb_agreement/article/preposition/word_order/plural/word_choice/other",
    )
    explanation: str = Field(..., description="中文错误说明")


class GrammarCorrectResponse(BaseModel):
    """语法纠错响应"""
    original_text: str = Field(..., description="用户输入的原文")
    corrected_text: str = Field(..., description="修正后的文本（最小改动）")
    errors: List[GrammarError] = Field(default_factory=list, description="逐项错误列表")
    polished_version: str = Field(default="", description="更地道的表达方式（可能改写句子）")
    suggestions: List[str] = Field(default_factory=list, description="2-4 条改进建议")