"""测评模块 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    """单道题目"""
    id: int = Field(..., description="题目 ID（动态生成时为负值）")
    type: str = Field(..., description="题型：speaking/reading/grammar")
    difficulty: str = Field(..., description="CEFR 难度")
    content: str = Field(..., description="题目文本")
    options: List[str] = Field(default_factory=list, description="客观题选项数组（口语题为空）")
    audio_base64: Optional[str] = Field(default=None, description="TTS 音频 base64 编码")


class AssessmentStartResponse(BaseModel):
    """测评开始响应 — 自适应难度，返回第一题"""
    session_id: str = Field(..., description="测评会话 UUID")
    question: QuestionItem = Field(..., description="第一道题目")
    total_questions: int = Field(..., description="总题数")
    current_difficulty: str = Field(..., description="当前难度 CEFR 等级")


class AssessmentAnswerResponse(BaseModel):
    """逐题提交响应 — 返回下一题或完成信号"""
    complete: bool = Field(..., description="是否已完成全部题目")
    next_question: Optional[QuestionItem] = Field(default=None, description="下一道题目（complete=true 时为 null）")
    current_difficulty: str = Field(..., description="当前自适应难度 CEFR 等级")


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


class QuestionResultItem(BaseModel):
    """单题答题结果"""
    order: int = Field(..., description="题号 1-10")
    type: str = Field(..., description="题型：speaking/reading/grammar")
    type_label: str = Field(..., description="题型中文名")
    difficulty: str = Field(..., description="CEFR 难度")
    content: str = Field(default="", description="题目文本（截取前60字）")
    user_answer: Optional[str] = Field(default=None, description="用户答案")
    correct_answer: Optional[str] = Field(default=None, description="正确答案（客观题）")
    is_correct: Optional[bool] = Field(default=None, description="是否正确")
    score: float = Field(default=0, description="该题得分 0-100")
    transcript: Optional[str] = Field(default=None, description="口语题转写文本")


class AssessmentSubmitResponse(BaseModel):
    """测评结果"""
    overall: float = Field(..., description="综合分 0-100")
    cefr_level: CEFRLevel = Field(..., description="CEFR 等级")
    dimension_scores: Dict[str, float] = Field(..., description="四维分数字典")
    weakness: Dict[str, Any] = Field(..., description="短板维度信息")
    duration: int = Field(..., description="测评用时（秒）")
    questions_detail: List[QuestionResultItem] = Field(default_factory=list, description="逐题详情")