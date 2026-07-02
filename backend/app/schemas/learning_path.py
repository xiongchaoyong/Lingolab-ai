"""学习路径模块 — 请求/响应 Schema"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


# ============================================================
# 每日任务
# ============================================================

class TaskItem(BaseModel):
    """单条任务"""
    id: int
    type: str = Field(..., description="shadowing / conversation / listening")
    title: str
    description: Optional[str] = ""
    difficulty: Optional[str] = None
    duration: str = Field(..., description="预估时长，如 '5-10分钟'")
    tag: Optional[str] = Field(default=None, description="展示标签")
    scene: Optional[str] = Field(default=None, description="对话场景标识")
    status: str = Field(default="pending", description="pending / skipped / completed")
    score: Optional[float] = None


class TaskProgress(BaseModel):
    """任务进度"""
    done: int = Field(..., description="已完成数")
    total: int = Field(..., description="总任务数")


class DailyTasksResponse(BaseModel):
    """每日任务响应"""
    date: str = Field(..., description="任务日期 YYYY-MM-DD")
    tasks: List[TaskItem]
    progress: TaskProgress


class SkipTaskRequest(BaseModel):
    """跳过任务请求"""
    reason: Optional[str] = Field(default=None, description="too_difficult / not_interested / null")


class AdjustDifficultyRequest(BaseModel):
    """调整难度请求"""
    direction: str = Field(..., description="easier / harder")


class TaskActionResponse(BaseModel):
    """任务操作响应"""
    status: str = "ok"
    task: Optional[TaskItem] = None


# ============================================================
# 历史记录
# ============================================================

class HistoryDay(BaseModel):
    """单日历史"""
    date: str = Field(..., description="日期标签")
    tasks: List[str] = Field(..., description="任务状态序列 done/skipped/pending")
    completed: int
    total: int
    minutes: int


class HistoryResponse(BaseModel):
    """历史记录响应"""
    records: List[HistoryDay]


# ============================================================
# 资料推荐
# ============================================================

class MaterialItem(BaseModel):
    """单条推荐资料"""
    id: int = Field(..., description="推荐记录 ID")
    material_id: str = Field(..., description="kg_nodes 中的 material 节点 ID")
    title: str
    url: str = ""
    type: str = Field(..., description="video / article / audio")
    difficulty: Optional[str] = None
    duration: Optional[str] = Field(default=None, description="时长/词数描述")
    tag: Optional[str] = Field(default=None, description="分类标签")
    cefr: Optional[str] = Field(default=None, description="CEFR 等级")
    score: float = Field(..., description="推荐分数")


class RecommendationsResponse(BaseModel):
    """资料推荐响应"""
    videos: List[MaterialItem]
    articles: List[MaterialItem]
    audios: List[MaterialItem]
    generated_at: str = Field(..., description="生成时间")


class DislikeResponse(BaseModel):
    """不感兴趣响应"""
    status: str = "disliked"


class ClickRequest(BaseModel):
    """点击/完成请求"""
    action: str = Field(..., description="view / complete")


class CompleteTaskRequest(BaseModel):
    """完成任务请求"""
    score: Optional[float] = Field(default=None, description="任务得分 0-100")
    duration_seconds: Optional[int] = Field(default=None, description="完成耗时（秒）")


# ============================================================
# 个人情况说明
# ============================================================

class DimensionScore(BaseModel):
    """单维度分数"""
    label: str = Field(..., description="维度中文名")
    key: str = Field(..., description="维度标识")
    score: Optional[float] = Field(default=None, description="分数 0-100")
    is_weakness: bool = Field(default=False, description="是否为短板")


class RecentStats(BaseModel):
    """近期练习统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    pronunciation_count: int = 0
    conversation_count: int = 0
    roleplay_count: int = 0
    avg_pronunciation_score: Optional[float] = None
    avg_conversation_score: Optional[float] = None


class RecommendationFactor(BaseModel):
    """推荐因子说明"""
    name: str
    weight: str
    description: str


class RecommendationLogic(BaseModel):
    """推荐算法说明"""
    algorithm: str = "四因子评分"
    factors: List[RecommendationFactor]


class ScoreLogItem(BaseModel):
    """维度分数变更日志条目"""
    id: int
    source: str = Field(..., description="触发来源标识")
    source_label: str = Field(..., description="触发来源中文名")
    listening_score: Optional[float] = None
    speaking_score: Optional[float] = None
    reading_score: Optional[float] = None
    grammar_score: Optional[float] = None
    overall_score: Optional[float] = None
    cefr_level: Optional[str] = None
    created_at: str = ""


class ProfileSummaryResponse(BaseModel):
    """个人情况说明响应"""
    cefr_level: str = "A1"
    level_source: str = ""          # "智能测评" / "自评" / "EMA动态"
    learning_goal: str = ""
    interests: List[str] = Field(default_factory=list)
    age_group: str = ""
    dimension_scores: List[DimensionScore] = Field(default_factory=list)
    recent_stats: RecentStats = Field(default_factory=RecentStats)
    recommendation_logic: RecommendationLogic = Field(default_factory=RecommendationLogic)
    score_logs: List[ScoreLogItem] = Field(default_factory=list)