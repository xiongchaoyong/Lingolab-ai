"""资料推荐 API — 个性化资料推荐"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.knowledge_graph import MaterialRecommendation
from app.services.recommendation import recommendation_service
from app.schemas.learning_path import (
    MaterialItem,
    ScoreFactor,
    RecommendationsResponse,
    DislikeResponse,
    ClickRequest,
)

router = APIRouter()

FACTOR_META = {
    "weakness": {"label": "短板匹配", "icon": "🎯"},
    "level": {"label": "难度适中", "icon": "📊"},
    "interest": {"label": "兴趣相关", "icon": "💡"},
    "novelty": {"label": "新鲜推荐", "icon": "🆕"},
}


def _build_score_factors(factors: dict) -> list:
    """将因子 dict 转为 ScoreFactor 列表（按权重降序）"""
    result = []
    for key in ["weakness", "level", "interest", "novelty"]:
        val = factors.get(key, 0)
        if val > 0:
            meta = FACTOR_META.get(key, {"label": key, "icon": ""})
            detail = _factor_detail(key, val)
            result.append(ScoreFactor(
                label=f"{meta['icon']} {meta['label']}",
                weight=val / 100,
                detail=detail,
            ))
    result.sort(key=lambda x: x.weight, reverse=True)
    return result


def _factor_detail(key: str, val: float) -> str:
    """为每个因子生成具体可读的说明"""
    score_label = "高度" if val >= 70 else "中等" if val >= 40 else "一般"
    if key == "weakness":
        return f"该资料针对你的学习短板，匹配度{score_label}"
    elif key == "level":
        return f"资料难度与你的CEFR等级匹配度{score_label}"
    elif key == "interest":
        return f"内容标签与你的兴趣偏好契合度{score_label}"
    elif key == "novelty":
        if val >= 70:
            return "近期未推荐过，是全新的学习内容"
        elif val >= 40:
            return "近期较少推荐，有一定新鲜度"
        else:
            return "最近推荐过类似内容，可回顾巩固"
    return ""


def _build_reason(factors: list) -> str:
    """根据因子生成推荐原因摘要"""
    if not factors:
        return ""
    # 取前2个最重要因子，生成自然语句
    parts = []
    for f in factors[:2]:
        parts.append(f.detail)
    return "；".join(parts)


@router.get("/", response_model=RecommendationsResponse)
def get_recommendations(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日个性化资料推荐（视频/文章/音频各2条）"""
    materials = recommendation_service.recommend_materials(current_user, db)
    recommendation_service.save_recommendations(current_user.id, materials, db)

    def to_items(group: str) -> list:
        items = []
        for m in materials.get(group, []):
            # 查找该推荐的记录 ID
            rec = (
                db.query(MaterialRecommendation)
                .filter(
                    MaterialRecommendation.user_id == current_user.id,
                    MaterialRecommendation.material_node_id == m["material_id"],
                )
                .order_by(MaterialRecommendation.created_at.desc())
                .first()
            )
            score_factors = _build_score_factors(m.get("score_factors", {}))
            items.append(MaterialItem(
                id=rec.id if rec else 0,
                material_id=m["material_id"],
                title=m["title"],
                url=m["url"],
                type=m["type"],
                difficulty=m["difficulty"],
                duration=m["duration"],
                tag=m["tag"],
                cefr=m["cefr"],
                score=m["score"],
                score_factors=score_factors,
                reason=_build_reason(score_factors),
            ))
        return items

    return RecommendationsResponse(
        videos=to_items("videos"),
        articles=to_items("articles"),
        generated_at=datetime.now().isoformat(),
    )


@router.post("/{recommendation_id}/dislike", response_model=DislikeResponse)
def dislike_recommendation(
    recommendation_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记推荐为不感兴趣"""
    rec = (
        db.query(MaterialRecommendation)
        .filter(
            MaterialRecommendation.id == recommendation_id,
            MaterialRecommendation.user_id == current_user.id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="推荐记录不存在")

    rec.action = "disliked"
    db.commit()

    return DislikeResponse(status="disliked")


@router.post("/refresh", response_model=RecommendationsResponse)
def refresh_recommendations(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """换一批推荐（重新计算），每日限 3 次"""
    refresh_count = recommendation_service.get_today_refresh_count(current_user.id, db)
    if refresh_count >= 3:
        raise HTTPException(status_code=429, detail="今日刷新次数已用完（每日限3次）")

    materials = recommendation_service.recommend_materials(current_user, db)
    recommendation_service.save_recommendations(current_user.id, materials, db)

    def to_items(group: str) -> list:
        items = []
        for m in materials.get(group, []):
            rec = (
                db.query(MaterialRecommendation)
                .filter(
                    MaterialRecommendation.user_id == current_user.id,
                    MaterialRecommendation.material_node_id == m["material_id"],
                )
                .order_by(MaterialRecommendation.created_at.desc())
                .first()
            )
            score_factors = _build_score_factors(m.get("score_factors", {}))
            items.append(MaterialItem(
                id=rec.id if rec else 0,
                material_id=m["material_id"],
                title=m["title"],
                url=m["url"],
                type=m["type"],
                difficulty=m["difficulty"],
                duration=m["duration"],
                tag=m["tag"],
                cefr=m["cefr"],
                score=m["score"],
                score_factors=score_factors,
                reason=_build_reason(score_factors),
            ))
        return items

    return RecommendationsResponse(
        videos=to_items("videos"),
        articles=to_items("articles"),
        generated_at=datetime.now().isoformat(),
    )


@router.post("/{recommendation_id}/click")
def click_recommendation(
    recommendation_id: int,
    body: ClickRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录点击/完成操作"""
    rec = (
        db.query(MaterialRecommendation)
        .filter(
            MaterialRecommendation.id == recommendation_id,
            MaterialRecommendation.user_id == current_user.id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="推荐记录不存在")

    if body.action == "view" and rec.action == "pending":
        rec.action = "viewed"
        rec.viewed_at = datetime.now()
    elif body.action == "complete":
        rec.action = "completed"

    db.commit()

    return {"status": "ok", "action": rec.action}