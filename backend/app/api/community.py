"""社区服务 API 路由 — 语音挑战 / 话题讨论"""

import logging

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.community import (
    ChallengeListResponse,
    ChallengeItem,
    LeaderboardResponse,
    LeaderboardItem,
    SubmissionResult,
    SubmissionItem,
    PostListResponse,
    PostItem,
    CommentListResponse,
    CommentItem,
    CreatePostRequest,
    CreateCommentRequest,
    LikeResponse,
)
from app.services.community import community_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 语音挑战
# ============================================================

@router.get("/challenges", response_model=ChallengeListResponse)
async def list_challenges(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取进行中的挑战列表"""
    items = community_service.get_active_challenges(db)
    db.commit()
    return ChallengeListResponse(challenges=[ChallengeItem(**i) for i in items])


@router.post("/challenges/{challenge_id}/submit", response_model=SubmissionResult)
async def submit_challenge(
    challenge_id: int,
    audio: UploadFile = File(..., description="录音文件"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交挑战录音"""
    import os
    import tempfile
    import subprocess

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        if len(content) < 1000:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="录音太短，请重新录制")

        # 转码为 16kHz WAV
        from app.services.audio_utils import convert_to_wav
        converted_path = convert_to_wav(tmp_path)

        result = community_service.submit_challenge(
            current_user.id, challenge_id, converted_path, db
        )
        db.commit()
        return SubmissionResult(
            submission=SubmissionItem(**result["submission"]),
            rank=result.get("rank"),
        )

    except subprocess.CalledProcessError:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="音频格式无法识别，请确认录音正常")
    finally:
        for path in (tmp_path, converted_path):
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass


@router.get("/challenges/{challenge_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    challenge_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取挑战排行榜"""
    result = community_service.get_leaderboard(challenge_id, db)
    db.commit()
    return LeaderboardResponse(
        challenge_id=result["challenge_id"],
        leaderboard=[LeaderboardItem(**i) for i in result["leaderboard"]],
    )


# ============================================================
# 话题讨论
# ============================================================

@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取帖子列表"""
    items = community_service.get_posts(current_user.id, db)
    db.commit()
    return PostListResponse(posts=[PostItem(**i) for i in items])


@router.post("/posts", response_model=PostItem)
async def create_post(
    body: CreatePostRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发帖"""
    result = community_service.create_post(current_user.id, body.topic, body.content, db)
    db.commit()
    return PostItem(**result)


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def toggle_like(
    post_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """切换点赞"""
    result = community_service.toggle_like(current_user.id, post_id, db)
    db.commit()
    return LikeResponse(**result)


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取评论列表"""
    items = community_service.get_comments(post_id, db)
    db.commit()
    return CommentListResponse(comments=[CommentItem(**i) for i in items])


@router.post("/posts/{post_id}/comments", response_model=CommentItem)
async def add_comment(
    post_id: int,
    body: CreateCommentRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发表评论"""
    result = community_service.add_comment(current_user.id, post_id, body.content, db)
    db.commit()
    return CommentItem(**result)


