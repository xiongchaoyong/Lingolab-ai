"""用户认证 API 路由"""

import logging

from fastapi import APIRouter, Depends, HTTPException
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

    redirect = "/assessment" if not user.assessment_completed else "/home"

    logger.info(f"用户登录: {user.username} (id={user.id})")

    return LoginResponse(
        user_id=user.id,
        username=user.username,
        token=token,
        assessment_completed=bool(user.assessment_completed),
        redirect=redirect,
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
        # 没有字段需要更新，直接返回当前画像
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
        )

    # 乐观锁
    current_version = current_user.version
    current_user.version = current_version + 1

    try:
        db.query(UserProfile).filter(
            UserProfile.id == current_user.id,
            UserProfile.version == current_version,
        ).update({
            "learning_goal": current_user.learning_goal,
            "interests": current_user.interests,
            "version": current_user.version,
        })
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        logger.error(f"画像更新失败: {e}")
        raise HTTPException(status_code=500, detail="画像更新失败，请稍后重试")

    # 检查是否发生并发冲突
    if current_user.version == current_version:
        # 更新未生效，可能是并发冲突
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
    )