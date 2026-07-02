"""安全工具 — JWT 令牌 + 密码哈希"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# JWT Bearer 安全方案
_bearer = HTTPBearer()

# 学习目标映射（前端英文值 → 数据库中文值）
LEARNING_GOAL_MAP = {
    "daily": "日常交流",
    "exam": "考试",
    "business": "商务",
    "abroad": "出国",
    "hobby": "兴趣爱好",
}


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int, username: str) -> str:
    """生成 JWT 访问令牌，有效期 24 小时"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str, verify_exp: bool = True) -> Optional[dict]:
    """解析 JWT 令牌，返回 payload；失败返回 None

    Args:
        verify_exp: 是否验证过期时间。刷新 Token 时传 False 允许过期令牌续期。
    """
    try:
        options = {"verify_exp": verify_exp} if not verify_exp else None
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options=options)
    except JWTError:
        return None


def get_age_group(age: int) -> str:
    """根据年龄返回年龄归类"""
    if age <= 12:
        return "儿童"
    elif age <= 17:
        return "青少年"
    elif age <= 22:
        return "大学生"
    elif age <= 50:
        return "职场"
    return "中老年"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """
    依赖注入：从 Authorization Header 解析 JWT，返回当前用户对象。
    供后续需要认证的接口复用。
    """
    from app.models.user import UserProfile

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    user = db.query(UserProfile).filter(
        UserProfile.id == payload.get("user_id"),
        UserProfile.is_active == 1,
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    return user