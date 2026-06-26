"""认证模块 — 请求/响应 Schema"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., description="用户名，4-20 字符，字母数字下划线")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码，8-32 字符，需包含字母和数字")
    age: int = Field(..., ge=1, le=150, description="年龄，1-150")
    learning_goal: str = Field(..., description="学习目标：daily/exam/business/abroad/hobby")
    interests: List[str] = Field(default_factory=list, description="兴趣标签数组")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 4 or len(v) > 20:
            raise ValueError("用户名需 4-20 个字符")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只允许字母、数字、下划线")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 32:
            raise ValueError("密码需 8-32 个字符")
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含字母和数字")
        return v

    @field_validator("learning_goal")
    @classmethod
    def validate_learning_goal(cls, v: str) -> str:
        valid = {"daily", "exam", "business", "abroad", "hobby"}
        if v not in valid:
            raise ValueError(f"无效的学习目标，可选值：{valid}")
        return v


class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    token: str = Field(..., description="JWT Token")
    assessment_completed: bool = Field(..., description="是否已完成测评")
    age_group: str = Field(..., description="年龄归类")


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """用户登录响应"""
    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    token: str = Field(..., description="JWT Token")
    assessment_completed: bool = Field(..., description="是否已完成测评")
    redirect: str = Field(..., description="跳转路径：测评页或首页")
    role: str = Field(default="learner", description="用户角色")
    avatar: Optional[str] = Field(default=None, description="头像URL")


class ProfileResponse(BaseModel):
    """用户画像响应"""
    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    age: int = Field(..., description="年龄")
    age_group: str = Field(..., description="年龄归类")
    learning_goal: str = Field(..., description="学习目标（中文）")
    interests: List[str] = Field(default_factory=list, description="兴趣标签")
    level_self: Optional[str] = Field(default=None, description="自评等级")
    level_test: Optional[str] = Field(default=None, description="测评等级")
    level_final: Optional[str] = Field(default=None, description="综合等级")
    assessment_completed: bool = Field(..., description="是否已完成测评")
    role: str = Field(..., description="用户角色")
    avatar: Optional[str] = Field(default=None, description="头像URL")


class ProfileUpdateRequest(BaseModel):
    """用户画像更新请求（仅允许修改学习目标和兴趣）"""
    learning_goal: Optional[str] = Field(default=None, description="学习目标：daily/exam/business/abroad/hobby")
    interests: Optional[List[str]] = Field(default=None, description="兴趣标签数组")

    @field_validator("learning_goal")
    @classmethod
    def validate_learning_goal(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"daily", "exam", "business", "abroad", "hobby"}
        if v not in valid:
            raise ValueError(f"无效的学习目标，可选值：{valid}")
        return v