"""用户认证 API 路由"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_age_group,
    get_current_user,
    LEARNING_GOAL_MAP,
)
from app.models.user import UserProfile
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.schemas.profile import ProfileScoresResponse, ProfileRefreshResponse


class RefreshResponse:
    """刷新 Token 响应"""
    def __init__(self):
        pass


# 手动定义 refresh 响应 schema，避免新建文件
from pydantic import BaseModel, Field


class TokenRefreshResponse(BaseModel):
    """Token 刷新响应"""
    token: str = Field(..., description="新的 JWT Token")
    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")


class AccountStatusRequest(BaseModel):
    """账号状态变更请求"""
    user_id: int = Field(..., description="目标用户 ID")
    is_active: int = Field(..., description="1-启用 0-禁用")

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册 — 创建账号并返回 JWT Token。
    注册成功后自动登录，前端引导跳转至水平测评页。
    """
    # 校验用户名唯一性
    existing_user = db.query(UserProfile).filter(
        UserProfile.username == req.username
    ).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="用户名已被注册")

    # 校验邮箱唯一性
    existing_email = db.query(UserProfile).filter(
        UserProfile.email == req.email
    ).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="邮箱已被注册")

    # 年龄归类 + 学习目标映射
    age_group = get_age_group(req.age)
    learning_goal_cn = LEARNING_GOAL_MAP.get(req.learning_goal, req.learning_goal)

    # 创建用户
    user = UserProfile(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        age=req.age,
        age_group=age_group,
        learning_goal=learning_goal_cn,
        interests=req.interests if req.interests else None,
        role="learner",
        assessment_completed=0,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"注册失败: {e}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")

    # 生成 JWT
    token = create_access_token(user.id, user.username)

    logger.info(f"新用户注册: {user.username} (id={user.id})")

    return RegisterResponse(
        user_id=user.id,
        username=user.username,
        token=token,
        assessment_completed=False,
        age_group=user.age_group,
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录 — 验证用户名密码并返回 JWT Token。
    登录后检查 assessment_completed 状态，决定跳转目标。
    """
    # 查找用户
    user = db.query(UserProfile).filter(
        UserProfile.username == req.username
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")

    # 生成 JWT
    token = create_access_token(user.id, user.username)

    if user.role == "teacher":
        redirect = "/teacher/dashboard"
    elif user.role == "admin":
        redirect = "/admin/dashboard"
    elif not user.assessment_completed:
        redirect = "/assessment"
    else:
        redirect = "/"

    logger.info(f"用户登录: {user.username} (id={user.id})")

    return LoginResponse(
        user_id=user.id,
        username=user.username,
        token=token,
        assessment_completed=bool(user.assessment_completed),
        redirect=redirect,
        role=user.role,
        avatar=user.avatar_url,
    )


# 学习目标反向映射（中文 → 前端英文值）
GOAL_REVERSE_MAP = {v: k for k, v in LEARNING_GOAL_MAP.items()}


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    获取当前用户画像。
    返回完整的用户画像信息，供前端设置页展示。
    """
    return ProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        age=current_user.age,
        age_group=current_user.age_group,
        learning_goal=GOAL_REVERSE_MAP.get(current_user.learning_goal, current_user.learning_goal),
        interests=current_user.interests or [],
        level_self=current_user.level_self,
        level_test=current_user.level_test,
        level_final=current_user.level_final,
        assessment_completed=bool(current_user.assessment_completed),
        role=current_user.role,
        avatar=current_user.avatar_url,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新用户画像 — 允许修改学习目标和兴趣标签。
    使用乐观锁防止并发冲突。
    """
    updated = False

    if req.learning_goal is not None:
        current_user.learning_goal = LEARNING_GOAL_MAP.get(req.learning_goal, req.learning_goal)
        updated = True

    if req.interests is not None:
        current_user.interests = req.interests
        updated = True

    if not updated:
        return ProfileResponse(
            user_id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            age=current_user.age,
            age_group=current_user.age_group,
            learning_goal=GOAL_REVERSE_MAP.get(current_user.learning_goal, current_user.learning_goal),
            interests=current_user.interests or [],
            level_self=current_user.level_self,
            level_test=current_user.level_test,
            level_final=current_user.level_final,
            assessment_completed=bool(current_user.assessment_completed),
            role=current_user.role,
            avatar=current_user.avatar_url,
        )

    # 乐观锁：version 字段防止并发冲突
    current_version = current_user.version
    current_user.version = current_version + 1

    try:
        affected = (
            db.query(UserProfile)
            .filter(
                UserProfile.id == current_user.id,
                UserProfile.version == current_version,
            )
            .update(
                {
                    "learning_goal": current_user.learning_goal,
                    "interests": current_user.interests,
                    "version": current_user.version,
                }
            )
        )
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        logger.error(f"画像更新失败: {e}")
        raise HTTPException(status_code=500, detail="画像更新失败，请稍后重试")

    if affected == 0:
        raise HTTPException(status_code=409, detail="画像已被更新，请刷新后重试")

    logger.info(f"用户画像更新: {current_user.username} (id={current_user.id})")

    return ProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        age=current_user.age,
        age_group=current_user.age_group,
        learning_goal=GOAL_REVERSE_MAP.get(current_user.learning_goal, current_user.learning_goal),
        interests=current_user.interests or [],
        level_self=current_user.level_self,
        level_test=current_user.level_test,
        level_final=current_user.level_final,
        assessment_completed=bool(current_user.assessment_completed),
        role=current_user.role,
        avatar=current_user.avatar_url,
    )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传用户头像。
    - 支持格式：jpg / jpeg / png / gif / webp
    - 最大 2MB
    - 覆盖式存储，以用户 ID 命名
    """
    # 校验文件大小
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="头像文件不能超过 2MB")

    # 校验图片类型
    allowed_types = {"jpg", "jpeg", "png", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext}，支持 jpg/png/gif/webp")

    # 用 Pillow 二次校验文件头
    from PIL import Image
    from io import BytesIO
    try:
        img = Image.open(BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="文件内容不是有效图片")

    # 保存头像
    avatar_dir = os.path.join("uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    filepath = os.path.join(avatar_dir, f"{current_user.id}.{ext}")
    with open(filepath, "wb") as f:
        f.write(contents)

    # 更新数据库
    avatar_url = f"/static/avatars/{current_user.id}.{ext}"
    current_user.avatar_url = avatar_url
    db.commit()

    logger.info(f"用户头像上传: {current_user.username} (id={current_user.id})")

    return {"avatar_url": avatar_url}


@router.get("/profile/scores", response_model=ProfileScoresResponse)
async def get_profile_scores(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户动态技能分数（EMA 计算的各维度分数 + 最近记录）"""
    from app.services.profile_updater import profile_updater

    dim_avgs = profile_updater.get_dimension_averages(current_user.id, db)
    recent = profile_updater.get_recent_scores(current_user.id, db)

    return ProfileScoresResponse(
        level_final=current_user.level_final,
        dimension_scores=dim_avgs,
        recent_scores=recent,
    )


@router.post("/profile/refresh", response_model=ProfileRefreshResponse)
async def refresh_profile(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发画像重算（基于最近 30 天练习数据）"""
    from app.services.profile_updater import profile_updater

    new_level, dim_avgs = profile_updater.recalculate(current_user.id, db)
    db.commit()

    return ProfileRefreshResponse(
        level_final=new_level,
        dimension_scores=dim_avgs,
        message="Profile refreshed successfully",
    )


@router.post("/token/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    刷新 JWT Token — 用当前有效 Token 换取新 Token。
    前端在 Token 即将过期时调用，实现无感续期。
    """
    new_token = create_access_token(current_user.id, current_user.username)
    logger.info(f"Token 刷新: {current_user.username} (id={current_user.id})")
    return TokenRefreshResponse(
        token=new_token,
        user_id=current_user.id,
        username=current_user.username,
    )


@router.post("/admin/toggle-status")
async def toggle_account_status(
    req: AccountStatusRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    管理员禁用/恢复用户账号。
    仅 admin 角色可调用，不能禁用自己。
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    if current_user.id == req.user_id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    target_user = db.query(UserProfile).filter(UserProfile.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    target_user.is_active = req.is_active
    db.commit()

    action = "恢复" if req.is_active else "禁用"
    logger.info(f"管理员 {current_user.username} {action}了用户 {target_user.username}")
    return {"message": f"用户 {target_user.username} 已{action}", "user_id": req.user_id, "is_active": req.is_active}