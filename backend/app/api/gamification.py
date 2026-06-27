"""游戏化闯关 API 路由"""

import os
import tempfile
import subprocess
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.gamification import (
    DailyChallengeResponse,
    ChallengeLevelItem,
    SubmitLevelResponse,
    CompleteChallengeResponse,
    DubbingContentItem,
    DubbingScoreResponse,
    DubbingRecordItem,
    BadgeItem,
    PointsRecord,
    PointsResponse,
    LeaderboardItem,
)
from app.services.gamification import (
    challenge_service,
    dubbing_service,
    PointsService,
    BadgeService,
    POINTS_RULES,
    DUBBING_CLIPS,
    BADGE_DEFINITIONS,
)
from app.services.profile_updater import profile_updater

router = APIRouter()
logger = logging.getLogger(__name__)


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV"""
    output_path = input_path + "_converted.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         output_path],
        check=True, capture_output=True,
    )
    return output_path


# ============================================================
# 每日闯关
# ============================================================

@router.get("/daily-challenge", response_model=DailyChallengeResponse)
async def get_daily_challenge(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日闯关内容（5关递增难度）"""
    result = challenge_service.get_daily_content(current_user.id, db)
    return DailyChallengeResponse(**result)


@router.post("/daily-challenge/submit", response_model=SubmitLevelResponse)
async def submit_challenge_level(
    audio: UploadFile = File(..., description="跟读录音"),
    level: int = Form(..., ge=1, le=5, description="关卡序号"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交单关录音进行评分"""
    if level < 1 or level > 5:
        raise HTTPException(status_code=422, detail="关卡序号必须为 1-5")

    # 获取关卡内容
    content = challenge_service.get_daily_content(current_user.id, db)
    level_data = content["levels"][level - 1]

    # 保存音频
    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content_bytes = await audio.read()
            tmp.write(content_bytes)
            tmp_path = tmp.name

        # 音频时长校验
        if len(content_bytes) < 1000:
            raise HTTPException(status_code=422, detail="录音太短，请重新录制")

        # 转码
        converted_path = convert_to_wav(tmp_path)

        # 发音评分
        result = await challenge_service.assess_level(
            converted_path, level_data["text"], "sentence"
        )

        overall = result["overall"]
        passed = overall >= level_data["pass_score"]

        # 持久化分数到画像
        try:
            profile_updater.ingest_pronunciation_scores(
                current_user.id, result.get("dimensions_list", []), source_id=0, db=db
            )
            db.commit()
        except Exception as e:
            logger.warning(f"持久化闯关分数失败: {e}")

        return SubmitLevelResponse(
            level=level,
            score=round(overall, 1),
            passed=passed,
            dimensions=result["dimensions"],
        )

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=422, detail="音频格式无法识别，请确认录音正常")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"评分服务不可用: {str(e)}")
    finally:
        for path in (tmp_path, converted_path):
            try:
                if path:
                    os.unlink(path)
                if path and os.path.exists(path + "_converted.wav"):
                    os.unlink(path + "_converted.wav")
            except Exception:
                pass


@router.post("/daily-challenge/complete", response_model=CompleteChallengeResponse)
async def complete_daily_challenge(
    levels_passed: int = Form(..., ge=0, le=5, description="通过的关卡数"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """完成每日闯关，发放积分和勋章"""
    all_completed = levels_passed == 5
    points_earned, new_badge_types = challenge_service.award_daily_points(
        current_user.id, levels_passed, all_completed, db
    )

    total_points = PointsService.get_total_points(current_user.id, db)

    # 提交事务
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="积分发放失败")

    new_badges = [
        BadgeItem(
            badge_type=bt,
            badge_name=BADGE_DEFINITIONS[bt]["name"],
            description=BADGE_DEFINITIONS[bt]["description"],
            earned=True,
        )
        for bt in new_badge_types
    ]

    return CompleteChallengeResponse(
        levels_passed=levels_passed,
        points_earned=points_earned,
        total_points=total_points,
        new_badges=new_badges,
    )


# ============================================================
# 配音挑战
# ============================================================

@router.get("/dubbing/content", response_model=list[DubbingContentItem])
async def get_dubbing_content(
    difficulty: str = Query(default=None, description="难度筛选 easy/medium/hard"),
    current_user: UserProfile = Depends(get_current_user),
):
    """获取配音内容列表"""
    clips = dubbing_service.get_content_list(difficulty)
    return [DubbingContentItem(**c) for c in clips]


@router.post("/dubbing/submit", response_model=DubbingScoreResponse)
async def submit_dubbing(
    audio: UploadFile = File(..., description="配音录音"),
    content_id: int = Form(..., description="配音内容ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交配音录音进行评分"""
    # 校验内容ID
    clip = next((c for c in DUBBING_CLIPS if c["id"] == content_id), None)
    if not clip:
        raise HTTPException(status_code=422, detail="配音内容不存在")

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content_bytes = await audio.read()
            tmp.write(content_bytes)
            tmp_path = tmp.name

        if len(content_bytes) < 1000:
            raise HTTPException(status_code=422, detail="录音太短，请重新录制")

        converted_path = convert_to_wav(tmp_path)

        # 配音评分
        result = await dubbing_service.score_dubbing(
            converted_path, content_id, current_user.id, db
        )
        db.commit()

        return DubbingScoreResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=422, detail="音频格式无法识别")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"评分服务不可用: {str(e)}")
    finally:
        for path in (tmp_path, converted_path):
            try:
                if path:
                    os.unlink(path)
            except Exception:
                pass


@router.get("/dubbing/records", response_model=list[DubbingRecordItem])
async def get_dubbing_records(
    limit: int = Query(default=20, ge=1, le=50),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户配音历史"""
    records = dubbing_service.get_user_records(current_user.id, db, limit)
    return [DubbingRecordItem(**r) for r in records]


# ============================================================
# 积分 & 勋章
# ============================================================

@router.get("/badges", response_model=list[BadgeItem])
async def get_user_badges(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户勋章列表（含未获得的）"""
    badges = BadgeService.get_user_badges(current_user.id, db)
    return [BadgeItem(**b) for b in badges]


@router.get("/points", response_model=PointsResponse)
async def get_user_points(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户积分总览"""
    total = PointsService.get_total_points(current_user.id, db)
    records = PointsService.get_recent_records(current_user.id, db)
    return PointsResponse(
        total_points=total,
        recent_records=[PointsRecord(**r) for r in records],
    )


@router.get("/leaderboard", response_model=list[LeaderboardItem])
async def get_leaderboard(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """获取积分排行榜"""
    rows = PointsService.get_leaderboard(db, limit)
    return [LeaderboardItem(**r) for r in rows]