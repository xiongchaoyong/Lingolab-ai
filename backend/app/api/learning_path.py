"""学习路径 API — 每日任务管理"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.knowledge_graph import DailyTask
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
)

router = APIRouter()


@router.get("/tasks", response_model=DailyTasksResponse)
def get_daily_tasks(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日任务列表（含进度）"""
    from datetime import date

    tasks = recommendation_service.generate_daily_tasks(current_user, db)
    done, total = recommendation_service.get_task_progress(current_user.id, db)

    task_items = []
    for t in tasks:
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