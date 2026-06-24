"""认证模块单元测试 — Schema 校验 + 安全工具函数"""

import pytest
from app.schemas.auth import RegisterRequest, LoginRequest, ProfileUpdateRequest
from app.core.security import (
    hash_password,
    verify_password,
    get_age_group,
    LEARNING_GOAL_MAP,
)


# ============================================================
# RegisterRequest — 字段校验测试
# ============================================================

class TestRegisterRequest:
    """用户注册请求 Schema 校验"""

    # --- username ---
    def test_username_valid(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="daily",
        )
        assert req.username == "test_user"

    def test_username_too_short(self):
        with pytest.raises(ValueError, match="用户名需 4-20 个字符"):
            RegisterRequest(
                username="abc",
                email="test@example.com",
                password="pass1234",
                age=20,
                learning_goal="daily",
            )

    def test_username_too_long(self):
        with pytest.raises(ValueError, match="用户名需 4-20 个字符"):
            RegisterRequest(
                username="a" * 21,
                email="test@example.com",
                password="pass1234",
                age=20,
                learning_goal="daily",
            )

    def test_username_special_chars(self):
        with pytest.raises(ValueError, match="用户名只允许字母、数字、下划线"):
            RegisterRequest(
                username="test user!",
                email="test@example.com",
                password="pass1234",
                age=20,
                learning_goal="daily",
            )

    def test_username_with_underscore_allowed(self):
        req = RegisterRequest(
            username="test_user_123",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="daily",
        )
        assert req.username == "test_user_123"

    # --- email ---
    def test_email_valid(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="daily",
        )
        assert req.email == "test@example.com"

    def test_email_invalid_no_at(self):
        with pytest.raises(ValueError, match="邮箱格式不正确"):
            RegisterRequest(
                username="test_user",
                email="invalid-email",
                password="pass1234",
                age=20,
                learning_goal="daily",
            )

    def test_email_invalid_no_domain(self):
        with pytest.raises(ValueError, match="邮箱格式不正确"):
            RegisterRequest(
                username="test_user",
                email="test@",
                password="pass1234",
                age=20,
                learning_goal="daily",
            )

    # --- password ---
    def test_password_too_short(self):
        with pytest.raises(ValueError, match="密码需 8-32 个字符"):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="Ab1",
                age=20,
                learning_goal="daily",
            )

    def test_password_no_digit(self):
        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="abcdefgh",
                age=20,
                learning_goal="daily",
            )

    def test_password_no_letter(self):
        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="12345678",
                age=20,
                learning_goal="daily",
            )

    def test_password_valid(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="abcd1234",
            age=20,
            learning_goal="daily",
        )
        assert req.username == "test_user"

    # --- age ---
    def test_age_min_boundary(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="pass1234",
            age=6,
            learning_goal="daily",
        )
        assert req.age == 6

    def test_age_below_min(self):
        with pytest.raises(ValueError):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="pass1234",
                age=5,
                learning_goal="daily",
            )

    def test_age_above_max(self):
        with pytest.raises(ValueError):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="pass1234",
                age=100,
                learning_goal="daily",
            )

    # --- learning_goal ---
    def test_learning_goal_valid(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="business",
        )
        assert req.learning_goal == "business"

    def test_learning_goal_invalid(self):
        with pytest.raises(ValueError, match="无效的学习目标"):
            RegisterRequest(
                username="test_user",
                email="test@example.com",
                password="pass1234",
                age=20,
                learning_goal="invalid_goal",
            )

    # --- interests 默认值 ---
    def test_interests_default_empty(self):
        req = RegisterRequest(
            username="test_user",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="daily",
        )
        assert req.interests == []


# ============================================================
# LoginRequest — 基本校验
# ============================================================

class TestLoginRequest:
    def test_login_request_valid(self):
        req = LoginRequest(username="test_user", password="pass1234")
        assert req.username == "test_user"
        assert req.password == "pass1234"


# ============================================================
# ProfileUpdateRequest — 可选字段校验
# ============================================================

class TestProfileUpdateRequest:
    def test_empty_update_allowed(self):
        req = ProfileUpdateRequest()
        assert req.learning_goal is None
        assert req.interests is None

    def test_valid_learning_goal(self):
        req = ProfileUpdateRequest(learning_goal="exam")
        assert req.learning_goal == "exam"

    def test_invalid_learning_goal(self):
        with pytest.raises(ValueError, match="无效的学习目标"):
            ProfileUpdateRequest(learning_goal="invalid")


# ============================================================
# security.py — 密码工具测试
# ============================================================

class TestPasswordFunctions:
    def test_hash_produces_different_from_input(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"

    def test_hash_is_deterministic_for_same_input(self):
        """同一个密码的哈希每次不同（bcrypt 加盐），但验证应通过"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt 每次生成不同盐值

    def test_verify_correct_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False


# ============================================================
# security.py — 年龄分组测试
# ============================================================

class TestAgeGroup:
    def test_child(self):
        assert get_age_group(6) == "儿童"
        assert get_age_group(12) == "儿童"

    def test_teenager(self):
        assert get_age_group(13) == "青少年"
        assert get_age_group(17) == "青少年"

    def test_college(self):
        assert get_age_group(18) == "大学生"
        assert get_age_group(22) == "大学生"

    def test_working(self):
        assert get_age_group(23) == "职场"
        assert get_age_group(50) == "职场"

    def test_senior(self):
        assert get_age_group(51) == "中老年"

    def test_boundary_age_12_to_13(self):
        assert get_age_group(12) == "儿童"
        assert get_age_group(13) == "青少年"


# ============================================================
# security.py — 学习目标映射测试
# ============================================================

class TestLearningGoalMap:
    def test_all_keys_exist(self):
        assert set(LEARNING_GOAL_MAP.keys()) == {"daily", "exam", "business", "abroad", "hobby"}

    def test_daily_maps_to_chinese(self):
        assert LEARNING_GOAL_MAP["daily"] == "日常交流"

    def test_exam_maps_to_chinese(self):
        assert LEARNING_GOAL_MAP["exam"] == "考试"