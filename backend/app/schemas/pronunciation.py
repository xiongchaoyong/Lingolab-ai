"""发音评测 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    label: str = Field(..., description="维度名称，如「音素准确度」")
    score: float = Field(..., description="维度得分 (0-100)")


class PronunciationError(BaseModel):
    phoneme: str = Field(..., description="错误音素")
    actual: str = Field(..., description="实际发音描述")
    tip: str = Field(..., description="纠正建议")
    score: float = Field(default=0.0, description="该音素得分")


class CharScore(BaseModel):
    char: str = Field(..., description="音素字符")
    score: float = Field(..., description="GOP 得分 (0-100)")
    duration_ms: float = Field(..., description="持续时间(ms)")
    level: str = Field(..., description="评级: 优秀/良好/一般/需练习")
    tip: str = Field(default="", description="发音指导（舌位/口型）")


class F0Point(BaseModel):
    t: float = Field(..., description="时间(秒)")
    hz: float = Field(..., description="基频(Hz)")


class StressVizData(BaseModel):
    chars: List[str] = Field(default_factory=list)
    energies: List[float] = Field(default_factory=list)
    durations: List[int] = Field(default_factory=list)
    is_stressed: List[bool] = Field(default_factory=list)
    energy_cv: float = 0.0
    dur_cv: float = 0.0


class IntonationVizData(BaseModel):
    direction: str = "unknown"
    range_st: float = 0.0
    f0_points: List[F0Point] = Field(default_factory=list)
    sentence_type: str = "statement"
    slope_st_per_sec: float = 0.0


class AnalysisDetail(BaseModel):
    stress: str = Field(default="", description="重音分析说明")
    intonation: str = Field(default="", description="语调分析说明")
    linking: str = Field(default="", description="连读分析说明")


class RhythmVizData(BaseModel):
    durations_ms: List[float] = Field(default_factory=list, description="各音素时长(ms)")
    chars: List[str] = Field(default_factory=list, description="对应音素字符")
    mean_ms: float = Field(default=0.0, description="平均音素时长(ms)")
    std_ms: float = Field(default=0.0, description="音素时长标准差(ms)")
    cv: float = Field(default=0.0, description="时长变异系数 (CV = std/mean)")
    pause_count: int = Field(default=0, description="异常停顿数 (时长>2x均值)")
    is_pause: List[bool] = Field(default_factory=list, description="各音素是否为异常停顿")


class LinkingPair(BaseModel):
    word_pair: str = Field(..., description="词对，如 'not at'")
    linkable: bool = Field(..., description="是否存在辅音-元音连读条件")
    last_phoneme: str = Field(default="", description="前词尾音素")
    first_phoneme: str = Field(default="", description="后词首音素")
    gap_ms: float = Field(default=0.0, description="词间间隙(ms)")
    score: float = Field(default=0.0, description="该词对连读得分 (0-100)")


class LinkingVizData(BaseModel):
    pairs: List[LinkingPair] = Field(default_factory=list, description="各词对连读分析")
    linkable_count: int = Field(default=0, description="存在连读条件的词对数")
    linked_count: int = Field(default=0, description="实际发生连读的词对数 (gap<=30ms)")
    avg_gap_ms: float = Field(default=0.0, description="平均词间间隙(ms)")


class PronunciationResponse(BaseModel):
    overall: float = Field(..., description="综合发音得分 (0-100)")
    dimensions: List[DimensionScore] = Field(..., description="各维度评分")
    errors: List[PronunciationError] = Field(..., description="错误音素定位")
    char_scores: List[CharScore] = Field(default_factory=list, description="字符级详细评分")
    analysis_detail: Optional[AnalysisDetail] = Field(default=None, description="维度分析详情说明")
    stress_viz: Optional[StressVizData] = Field(default=None, description="重音可视化数据")
    intonation_viz: Optional[IntonationVizData] = Field(default=None, description="语调可视化数据")
    linking_viz: Optional[LinkingVizData] = Field(default=None, description="连读可视化数据")
    rhythm_viz: Optional[RhythmVizData] = Field(default=None, description="节奏可视化数据")


class ContentItem(BaseModel):
    """跟读内容条目"""
    id: int
    title: str
    content_text: str
    content_type: str
    cefr_level: str
    category: Optional[str] = None
    phonetic_ipa: Optional[str] = None

    class Config:
        from_attributes = True


class RecordItem(BaseModel):
    """评测历史记录"""
    id: int
    content_id: int
    mode: str
    overall_score: float
    phoneme_score: Optional[float] = None
    stress_score: Optional[float] = None
    created_at: Any = None
    content_title: Optional[str] = None
    content_text: Optional[str] = None

    class Config:
        from_attributes = True
