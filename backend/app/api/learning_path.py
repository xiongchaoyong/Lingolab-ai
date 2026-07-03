"""学习路径 API — 每日任务管理 + 个人情况说明"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.knowledge_graph import DailyTask
from app.models.profile import UserSkillScore
from app.services.recommendation import recommendation_service
from app.services.profile_updater import profile_updater
from app.schemas.learning_path import (
    TaskItem,
    DailyTasksResponse,
    TaskProgress,
    SkipTaskRequest,
    AdjustDifficultyRequest,
    TaskActionResponse,
    HistoryDay,
    HistoryResponse,
    CompleteTaskRequest,
    DimensionScore,
    RecentStats,
    RecommendationFactor,
    RecommendationLogic,
    ProfileSummaryResponse,
    ScoreLogItem,
)

router = APIRouter()


def _build_task_reason(task_type: str, weakness_label: str, user_goal: str) -> str:
    """根据任务类型生成推荐原因"""
    reasons = {
        "shadowing": f"针对你的「{weakness_label}」短板，通过跟读训练改善发音",
        "conversation": f"匹配你的学习目标「{user_goal}」，实战练习口语表达",
        "grammar": f"针对你的「{weakness_label}」短板，通过语法纠错提升准确性",
        "vocabulary": f"针对你的「{weakness_label}」短板，通过词汇积累扩充表达能力",
    }
    return reasons.get(task_type, "")


@router.get("/tasks", response_model=DailyTasksResponse)
def get_daily_tasks(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日任务列表（含进度）"""
    from datetime import date

    tasks = recommendation_service.generate_daily_tasks(current_user, db)
    done, total = recommendation_service.get_task_progress(current_user.id, db)

    # 推荐原因所需的上下文
    DIM_LABELS = {
        "pronunciation": "发音", "fluency": "流利度",
        "vocabulary": "词汇运用", "grammar": "语法",
    }
    weakness_dim = recommendation_service.get_weakness_dimension(current_user, db)
    weakness_label = DIM_LABELS.get(weakness_dim, weakness_dim)
    user_goal = current_user.learning_goal or "日常交流"

    task_items = []
    for t in tasks:
        reason = _build_task_reason(t["type"], weakness_label, user_goal)
        task_items.append(TaskItem(
            id=t["id"],
            type=t["type"],
            title=t["title"],
            description=t.get("description", ""),
            difficulty=t.get("difficulty"),
            duration=t.get("duration", "5-10分钟"),
            tag=t.get("tag"),
            scene=t.get("scene"),
            status=t.get("status", "pending"),
            score=t.get("score"),
            reason=reason,
        ))

    return DailyTasksResponse(
        date=date.today().isoformat(),
        tasks=task_items,
        progress=TaskProgress(done=done, total=total),
    )


@router.post("/tasks/{task_id}/skip", response_model=TaskActionResponse)
def skip_task(
    task_id: int,
    body: SkipTaskRequest = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """跳过某条任务"""
    reason = body.reason if body else None
    result = recommendation_service.skip_task(task_id, current_user.id, reason, db)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskActionResponse(
        status="ok",
        task=TaskItem(
            id=result["id"],
            type=result["type"],
            title=result["title"],
            status=result["status"],
            duration="",
        ),
    )


@router.post("/tasks/{task_id}/replace", response_model=TaskActionResponse)
def replace_task(
    task_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """换一个同类型任务"""
    result = recommendation_service.replace_task(task_id, current_user.id, current_user, db)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskActionResponse(
        status="ok",
        task=TaskItem(
            id=result["id"],
            type=result["type"],
            title=result["title"],
            description=result.get("description", ""),
            difficulty=result.get("difficulty"),
            duration=result.get("duration", "5-10分钟"),
            tag=result.get("tag"),
            scene=result.get("scene"),
            status=result.get("status", "pending"),
            score=result.get("score"),
        ),
    )


@router.post("/tasks/{task_id}/adjust-difficulty", response_model=TaskActionResponse)
def adjust_difficulty(
    task_id: int,
    body: AdjustDifficultyRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """调整任务难度"""
    result = recommendation_service.adjust_difficulty(task_id, current_user.id, body.direction, db)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="无法调整难度")

    return TaskActionResponse(
        status="ok",
        task=TaskItem(
            id=result["id"],
            type=result["type"],
            title=result["title"],
            difficulty=result.get("difficulty"),
            status=result.get("status", "pending"),
            duration="",
        ),
    )


@router.post("/tasks/{task_id}/complete", response_model=TaskActionResponse)
def complete_task(
    task_id: int,
    body: CompleteTaskRequest = CompleteTaskRequest(),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记任务完成并记录分数"""
    task = (
        db.query(DailyTask)
        .filter(DailyTask.id == task_id, DailyTask.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "completed"
    if body.score is not None:
        task.score = body.score
    if body.duration_seconds is not None:
        task.duration_seconds = body.duration_seconds
    task.completed_at = datetime.now()
    db.flush()

    # 摄入分数到动态画像
    profile_updater.ingest_task_score(current_user.id, task, db)
    db.commit()

    return TaskActionResponse(
        status="ok",
        task=TaskItem(
            id=task.id,
            type=task.task_type,
            title=task.title,
            description=task.description or "",
            difficulty=task.difficulty,
            duration="",
            status="completed",
            score=float(task.score) if task.score else None,
        ),
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    days: int = Query(default=7, ge=1, le=90, description="查询天数"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取历史学习记录"""
    records = recommendation_service.get_history(current_user.id, days, db)

    history_days = [
        HistoryDay(
            date=r["date"],
            tasks=r["tasks"],
            completed=r["completed"],
            total=r["total"],
            minutes=r["minutes"],
        )
        for r in records
    ]

    return HistoryResponse(records=history_days)


@router.get("/profile-summary", response_model=ProfileSummaryResponse)
def get_profile_summary(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取个人情况说明 — 解释推荐依据"""
    # 维度中文标签
    DIM_LABELS = {
        "pronunciation": "发音", "fluency": "流利度",
        "vocabulary": "词汇运用", "grammar": "语法",
    }

    # 1. 用户基础信息
    level_source = "自评"
    if current_user.level_test:
        level_source = "智能测评"
    if current_user.level_final and current_user.level_final != current_user.level_test:
        level_source = "EMA动态更新"

    # 2. EMA 维度分数
    dim_avgs = profile_updater.get_dimension_averages(current_user.id, db)
    weakness_dim = recommendation_service.get_weakness_dimension(current_user, db)

    dimension_scores = []
    for key, label in DIM_LABELS.items():
        dimension_scores.append(DimensionScore(
            label=label,
            key=key,
            score=dim_avgs.get(key),
            is_weakness=(key == weakness_dim),
        ))

    # 3. 近期练习统计（近30天）
    cutoff = datetime.utcnow() - timedelta(days=30)
    skill_scores = (
        db.query(UserSkillScore)
        .filter(UserSkillScore.user_id == current_user.id, UserSkillScore.created_at >= cutoff)
        .all()
    )

    pronunciation_scores = [s for s in skill_scores if s.source == "pronunciation"]
    conversation_scores = [s for s in skill_scores if s.source == "conversation"]
    roleplay_scores = [s for s in skill_scores if s.source == "roleplay"]

    tasks_count = (
        db.query(func.count(DailyTask.id))
        .filter(DailyTask.user_id == current_user.id, DailyTask.task_date >= cutoff.date())
        .scalar()
    ) or 0
    completed_count = (
        db.query(func.count(DailyTask.id))
        .filter(DailyTask.user_id == current_user.id, DailyTask.task_date >= cutoff.date(), DailyTask.status == "completed")
        .scalar()
    ) or 0

    def avg_score(scores):
        vals = [float(s.score) for s in scores]
        return round(sum(vals) / len(vals), 1) if vals else None

    recent_stats = RecentStats(
        total_tasks=tasks_count,
        completed_tasks=completed_count,
        pronunciation_count=len(pronunciation_scores),
        conversation_count=len(conversation_scores),
        roleplay_count=len(roleplay_scores),
        avg_pronunciation_score=avg_score(pronunciation_scores),
        avg_conversation_score=avg_score(conversation_scores),
    )

    # 4. 推荐算法说明
    weakness_label = DIM_LABELS.get(weakness_dim, weakness_dim)
    interests_text = "、".join(current_user.interests[:3]) if current_user.interests else "暂无"
    level_text = current_user.level_final or "A1"

    recommendation_logic = RecommendationLogic(
        algorithm="四因子评分模型",
        factors=[
            RecommendationFactor(
                name="短板匹配",
                weight="40%",
                description=f"你的「{weakness_label}」维度得分较低，系统优先推荐该维度的练习内容，帮助补齐短板",
            ),
            RecommendationFactor(
                name="难度匹配",
                weight="35%",
                description=f"匹配 CEFR {level_text} 等级的内容，确保难度适中，既不会太简单也不会太难",
            ),
            RecommendationFactor(
                name="兴趣匹配",
                weight="25%",
                description=f"结合你的兴趣偏好（{interests_text}），推荐更符合个人喜好的学习资料",
            ),
            RecommendationFactor(
                name="新颖度去重",
                weight="乘性因子",
                description="7天内已推荐过的资料会降低权重，标记为「不感兴趣」的资料不再推荐",
            ),
        ],
    )

    return ProfileSummaryResponse(
        cefr_level=current_user.level_final or "A1",
        level_source=level_source,
        learning_goal=current_user.learning_goal or "未设置",
        interests=current_user.interests or [],
        age_group=current_user.age_group or "",
        dimension_scores=dimension_scores,
        recent_stats=recent_stats,
        recommendation_logic=recommendation_logic,
        score_logs=profile_updater.get_score_logs(current_user.id, db),
    )