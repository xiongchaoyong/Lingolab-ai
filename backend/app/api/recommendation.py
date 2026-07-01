"""资料推荐 API — 个性化资料推荐"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.learning import LearningMaterial
from app.models.knowledge_graph import MaterialRecommendation
from app.services.recommendation import recommendation_service
from app.services.knowledge_graph import kg_service
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


@router.get("/material/{material_id}")
def get_material_detail(
    material_id: str,
    material_type: Optional[str] = Query(default=None, description="资料类型过滤：video/article/audio"),
    db: Session = Depends(get_db),
):
    """获取单个学习资料详情

    支持两种查询方式：
    1. 数字 ID → 从 learning_materials 表查询
    2. kg_nodes 格式（如 material:audio_1）→ 从知识图谱节点查询
    """
    # 尝试按 kg_nodes ID 查询
    node_attrs = kg_service.get_node(material_id)
    if node_attrs and node_attrs.get("type") == "material":
        node = {"id": material_id, **node_attrs}  # get_node 不返回 id，手动补充
        extra = node.get("extra_data", {}) or {}
        sub_type = node.get("sub_type", "article")

        # 尝试从 learning_materials 表匹配（按标题标签匹配）
        material = (
            db.query(LearningMaterial)
            .filter(
                LearningMaterial.title == node["label"],
                LearningMaterial.is_active == 1,
            )
            .first()
        )

        if material:
            # 类型过滤
            if material_type and material.material_type != material_type:
                raise HTTPException(status_code=404, detail=f"资料类型不匹配，期望 {material_type}，实际 {material.material_type}")

            return {
                "id": material.id,
                "title": material.title,
                "description": material.description or "",
                "material_type": material.material_type,
                "url": material.url,
                "cefr_level": material.cefr_level,
                "category": material.category or "",
                "tags": material.tags or [],
                "duration_seconds": material.duration_seconds,
                "focus_dimensions": material.focus_dimensions or [],
            }

        # 回退：从 kg_node 构造返回数据
        return {
            "id": node["id"],
            "title": node["label"],
            "description": extra.get("description", ""),
            "material_type": sub_type,
            "url": extra.get("url", ""),
            "cefr_level": extra.get("difficulty", "A1"),
            "category": extra.get("category", ""),
            "tags": extra.get("tags", []),
            "duration_seconds": extra.get("duration_seconds"),
            "focus_dimensions": extra.get("focus_dimensions", []),
        }

    # 按数字 ID 查询 learning_materials
    try:
        numeric_id = int(material_id)
        material = (
            db.query(LearningMaterial)
            .filter(LearningMaterial.id == numeric_id, LearningMaterial.is_active == 1)
            .first()
        )
        if material:
            if material_type and material.material_type != material_type:
                raise HTTPException(status_code=404, detail=f"资料类型不匹配，期望 {material_type}，实际 {material.material_type}")

            return {
                "id": material.id,
                "title": material.title,
                "description": material.description or "",
                "material_type": material.material_type,
                "url": material.url,
                "cefr_level": material.cefr_level,
                "category": material.category or "",
                "tags": material.tags or [],
                "duration_seconds": material.duration_seconds,
                "focus_dimensions": material.focus_dimensions or [],
            }
    except ValueError:
        pass

    raise HTTPException(status_code=404, detail="资料不存在")