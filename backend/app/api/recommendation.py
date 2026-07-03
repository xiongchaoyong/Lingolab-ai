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
            result.append(ScoreFactor(label=meta["label"], weight=val / 100, detail=detail))
    result.sort(key=lambda x: x.weight, reverse=True)
    return result


def _factor_detail(key: str, val: float) -> str:
    if key == "weakness":
        return "针对你的学习短板"
    elif key == "level":
        return f"匹配你的语言等级（{val:.0f}%符合）"
    elif key == "interest":
        return "与你的兴趣标签一致"
    elif key == "novelty":
        return "最近未推荐过的新内容"
    return ""


def _build_reason(factors: list) -> str:
    """根据因子生成推荐原因摘要"""
    if not factors:
        return ""
    labels = [f.label for f in factors[:2]]
    return "、".join(labels)


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
        audios=to_items("audios"),
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
        audios=to_items("audios"),
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