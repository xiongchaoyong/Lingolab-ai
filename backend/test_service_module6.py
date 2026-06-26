"""服务模块6（管理服务）单元测试 — 资料推荐 + 教师管理 + 运营管理"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.learning_path import (
    MaterialItem,
    RecommendationsResponse,
    DislikeResponse,
    ClickRequest,
)
from app.schemas.admin import (
    ClassItem,
    ClassListResponse,
    CreateClassRequest,
    JoinClassRequest,
    StudentItem,
    StudentListResponse,
    AssignmentItem,
    AssignmentListResponse,
    CreateAssignmentRequest,
    SubmissionItem,
    SubmissionListResponse,
    ReviewRequest,
    UserListItem,
    UserListResponse,
    UserStatusRequest,
    DashboardMetrics,
    TrendPoint,
    DashboardResponse,
    FeedbackItem,
    FeedbackListResponse,
    FeedbackReplyRequest,
    FeedbackStatusRequest,
)


# ============================================================
# 资料推荐 Schema
# ============================================================

class TestRecommendationSchemas:
    """资料推荐 Schema 验证"""

    def test_material_item(self):
        item = MaterialItem(
            id=1, material_id="10", title="Daily English", url="https://example.com",
            type="video", difficulty="B1", duration="5min", tag="日常", cefr="B1", score=85.5,
        )
        assert item.type == "video"
        assert item.score == 85.5

    def test_recommendations_response(self):
        resp = RecommendationsResponse(
            videos=[MaterialItem(id=1, material_id="1", title="V1", url="#", type="video", difficulty="B1", duration="5m", tag="t", cefr="B1", score=80)],
            articles=[MaterialItem(id=2, material_id="2", title="A1", url="#", type="article", difficulty="B1", duration="3m", tag="t", cefr="B1", score=75)],
            audios=[MaterialItem(id=3, material_id="3", title="Au1", url="#", type="audio", difficulty="B1", duration="4m", tag="t", cefr="B1", score=70)],
            generated_at="2026-06-26T00:00:00",
        )
        assert len(resp.videos) == 1
        assert len(resp.articles) == 1
        assert len(resp.audios) == 1

    def test_dislike_response(self):
        resp = DislikeResponse(status="disliked")
        assert resp.status == "disliked"

    def test_click_request(self):
        req = ClickRequest(action="view")
        assert req.action == "view"

    def test_click_request_complete(self):
        req = ClickRequest(action="complete")
        assert req.action == "complete"


# ============================================================
# 班级管理 Schema
# ============================================================

class TestClassSchemas:
    """班级 Schema 验证"""

    def test_class_item(self):
        item = ClassItem(
            id=1, name="初级口语班", description="A1-A2", level_range="A1-A2",
            student_count=15, invite_code="ABC123",
        )
        assert item.student_count == 15
        assert item.invite_code == "ABC123"

    def test_class_list(self):
        resp = ClassListResponse(classes=[
            ClassItem(id=i, name=f"班级{i}") for i in range(3)
        ])
        assert len(resp.classes) == 3

    def test_create_class_request(self):
        req = CreateClassRequest(name="新班级", description="描述", level_range="B1-B2")
        assert req.name == "新班级"

    def test_join_class_request(self):
        req = JoinClassRequest(invite_code="ABC123")
        assert req.invite_code == "ABC123"


# ============================================================
# 学生 Schema
# ============================================================

class TestStudentSchemas:
    """学生 Schema 验证"""

    def test_student_item(self):
        item = StudentItem(id=1, username="student1", level_final="B1", total_minutes=120)
        assert item.total_minutes == 120

    def test_student_list(self):
        resp = StudentListResponse(students=[
            StudentItem(id=i, username=f"s{i}") for i in range(5)
        ])
        assert len(resp.students) == 5


# ============================================================
# 作业管理 Schema
# ============================================================

class TestAssignmentSchemas:
    """作业 Schema 验证"""

    def test_assignment_item(self):
        item = AssignmentItem(
            id=1, class_id=1, title="跟读作业", content_type="pronunciation",
            content_ids=[1, 2, 3], due_date="2026-07-01", completion_rate=0.6,
        )
        assert item.completion_rate == 0.6
        assert len(item.content_ids) == 3

    def test_assignment_list(self):
        resp = AssignmentListResponse(assignments=[
            AssignmentItem(id=i, class_id=1, title=f"作业{i}", content_type="pronunciation")
            for i in range(3)
        ])
        assert len(resp.assignments) == 3

    def test_create_assignment_request(self):
        req = CreateAssignmentRequest(
            class_id=1, title="跟读作业", content_type="pronunciation",
            content_ids=[1, 2], due_date="2026-07-01",
        )
        assert req.content_type == "pronunciation"

    def test_submission_item(self):
        item = SubmissionItem(
            id=1, user_id=1, assignment_id=1, score=85.0,
            teacher_feedback="很好", teacher_score=90.0, status="reviewed",
        )
        assert item.status == "reviewed"
        assert item.teacher_score == 90.0

    def test_submission_list(self):
        resp = SubmissionListResponse(submissions=[
            SubmissionItem(id=i, user_id=i, assignment_id=1) for i in range(5)
        ])
        assert len(resp.submissions) == 5

    def test_review_request(self):
        req = ReviewRequest(teacher_feedback="发音很好", teacher_score=90)
        assert req.teacher_score == 90


# ============================================================
# 用户管理 Schema
# ============================================================

class TestUserManagementSchemas:
    """用户管理 Schema 验证"""

    def test_user_list_item(self):
        item = UserListItem(
            id=1, username="user1", role="student", level_final="B1",
            total_minutes=500, is_active=1, assessment_completed=1,
        )
        assert item.is_active == 1

    def test_user_list_response(self):
        resp = UserListResponse(
            users=[UserListItem(id=i, username=f"u{i}", role="student") for i in range(10)],
            total=100,
        )
        assert resp.total == 100
        assert len(resp.users) == 10

    def test_user_status_request(self):
        req = UserStatusRequest(is_active=0)
        assert req.is_active == 0


# ============================================================
# 仪表盘 Schema
# ============================================================

class TestDashboardSchemas:
    """仪表盘 Schema 验证"""

    def test_dashboard_metrics(self):
        m = DashboardMetrics(dau=50, mau=200, retention_d1=0.6, retention_d7=0.3, total_users=500, active_users=200)
        assert m.dau == 50
        assert m.retention_d7 == 0.3

    def test_trend_point(self):
        p = TrendPoint(label="2026-06-01", value=10)
        assert p.value == 10

    def test_dashboard_response(self):
        resp = DashboardResponse(
            metrics=DashboardMetrics(dau=50, mau=200),
            user_trend=[TrendPoint(label=f"06-{i}", value=i * 10) for i in range(1, 8)],
            content_type_distribution={"pronunciation": 30, "conversation": 20},
            level_distribution={"A1": 10, "B1": 30},
        )
        assert len(resp.user_trend) == 7
        assert resp.content_type_distribution["pronunciation"] == 30


# ============================================================
# 反馈管理 Schema
# ============================================================

class TestFeedbackSchemas:
    """反馈 Schema 验证"""

    def test_feedback_item(self):
        item = FeedbackItem(
            id=1, user_id=1, content="界面很好看", feedback_type="ui",
            status="pending", admin_reply=None,
        )
        assert item.status == "pending"

    def test_feedback_list(self):
        resp = FeedbackListResponse(
            feedbacks=[FeedbackItem(id=i, user_id=1, content=f"反馈{i}") for i in range(5)],
            total=20,
        )
        assert resp.total == 20

    def test_feedback_reply_request(self):
        req = FeedbackReplyRequest(reply="感谢您的反馈！")
        assert req.reply == "感谢您的反馈！"

    def test_feedback_status_request(self):
        req = FeedbackStatusRequest(status="resolved")
        assert req.status == "resolved"

    def test_feedback_status_validation(self):
        """status 只能是 pending 或 resolved"""
        with pytest.raises(Exception):
            FeedbackStatusRequest(status="invalid")
