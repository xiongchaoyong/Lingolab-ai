"""测评模块 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    """单道题目"""
    id: int = Field(..., description="题目 ID")
    type: str = Field(..., description="题型：listening/speaking/reading/grammar")
    difficulty: str = Field(..., description="CEFR 难度")
    content: str = Field(..., description="题目文本")
    options: List[str] = Field(default_factory=list, description="客观题选项数组（口语题为空）")


class AssessmentStartResponse(BaseModel):
    """测评开始响应"""
    session_id: str = Field(..., description="测评会话 UUID")
    questions: List[QuestionItem] = Field(..., description="10 道题目")


class AnswerItem(BaseModel):
    """单题答案"""
    question_id: int = Field(..., description="题目 ID")
    answer: Optional[str] = Field(default=None, description="客观题：选项字母 A/B/C/D，口语题：null")


class AssessmentSubmitRequest(BaseModel):
    """提交测评答案"""
    session_id: str = Field(..., description="测评会话 UUID")
    answers: List[AnswerItem] = Field(..., description="所有题目的答案")


class DimensionScore(BaseModel):
    """单维度得分"""
    label: str = Field(..., description="维度中文名")
    score: float = Field(..., description="得分 0-100")


class CEFRLevel(BaseModel):
    """CEFR 等级"""
    level: str = Field(..., description="等级：A1/A2/B1/B2/C1/C2")
    label: str = Field(..., description="等级中文描述")


class AssessmentSubmitResponse(BaseModel):
    """测评结果"""
    overall: float = Field(..., description="综合分 0-100")
    cefr_level: CEFRLevel = Field(..., description="CEFR 等级")
    dimension_scores: Dict[str, float] = Field(..., description="四维分数字典")
    weakness: Dict[str, Any] = Field(..., description="短板维度信息")
    duration: int = Field(..., description="测评用时（秒）")