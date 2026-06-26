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
    RecommendationsResponse,
    DislikeResponse,
    ClickRequest,
)

router = APIRouter()


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