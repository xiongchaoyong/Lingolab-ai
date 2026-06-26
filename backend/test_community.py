"""社区服务模块单元测试 — Schema 验证"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.community import (
    ChallengeItem,
    ChallengeListResponse,
    SubmissionItem,
    LeaderboardItem,
    LeaderboardResponse,
    SubmissionResult,
    PostItem,
    PostListResponse,
    CreatePostRequest,
    CommentItem,
    CommentListResponse,
    CreateCommentRequest,
    LikeResponse,
    GroupItem,
    GroupListResponse,
    JoinResult,
)


# ============================================================
# 语音挑战 Schema
# ============================================================

class TestChallengeSchemas:
    """挑战 Schema 验证"""

    def test_challenge_item(self):
        item = ChallengeItem(
            id=1, title="每日跟读", sample_text="Hello world",
            deadline="2026-07-01", participants_count=10,
        )
        assert item.id == 1
        assert item.participants_count == 10

    def test_challenge_list(self):
        resp = ChallengeListResponse(challenges=[
            ChallengeItem(id=i, title=f"挑战{i}", sample_text="text", deadline="2026-07-01")
            for i in range(3)
        ])
        assert len(resp.challenges) == 3

    def test_submission_item(self):
        item = SubmissionItem(
            id=1, user_id=1, challenge_id=1, audio_url="/uploads/test.webm",
            pronunciation_score=85, fluency_score=80, total_score=82,
        )
        assert item.total_score == 82

    def test_leaderboard_item(self):
        item = LeaderboardItem(rank=1, user_id=1, username="test", total_score=95)
        assert item.rank == 1

    def test_leaderboard_response(self):
        resp = LeaderboardResponse(
            challenge_id=1,
            leaderboard=[LeaderboardItem(rank=i, user_id=i, username=f"user{i}") for i in range(1, 6)],
        )
        assert resp.challenge_id == 1
        assert len(resp.leaderboard) == 5

    def test_submission_result(self):
        result = SubmissionResult(
            submission=SubmissionItem(id=1, user_id=1, challenge_id=1, audio_url="/test.webm"),
            rank=3,
        )
        assert result.rank == 3


# ============================================================
# 话题讨论 Schema
# ============================================================

class TestPostSchemas:
    """帖子 Schema 验证"""

    def test_post_item(self):
        post = PostItem(
            id=1, user_id=1, username="test", topic="学习心得",
            content="今天学了发音", likes_count=5, comments_count=3, is_liked=True,
        )
        assert post.likes_count == 5
        assert post.is_liked is True

    def test_post_list(self):
        resp = PostListResponse(posts=[
            PostItem(id=i, user_id=1, topic=f"帖子{i}", content="content") for i in range(5)
        ])
        assert len(resp.posts) == 5

    def test_create_post_request(self):
        req = CreatePostRequest(topic="学习心得", content="今天练习了发音")
        assert req.topic == "学习心得"

    def test_create_post_validation(self):
        """标题最长 200 字符"""
        with pytest.raises(Exception):
            CreatePostRequest(topic="x" * 201, content="test")


class TestCommentSchemas:
    """评论 Schema 验证"""

    def test_comment_item(self):
        comment = CommentItem(id=1, user_id=1, username="test", content="说得很好！")
        assert comment.content == "说得很好！"

    def test_comment_list(self):
        resp = CommentListResponse(comments=[
            CommentItem(id=i, user_id=1, content=f"评论{i}") for i in range(3)
        ])
        assert len(resp.comments) == 3

    def test_create_comment_request(self):
        req = CreateCommentRequest(content="说得很好！")
        assert req.content == "说得很好！"


class TestLikeSchema:
    """点赞 Schema 验证"""

    def test_like_response(self):
        resp = LikeResponse(liked=True, likes_count=6)
        assert resp.liked is True
        assert resp.likes_count == 6

    def test_unlike_response(self):
        resp = LikeResponse(liked=False, likes_count=4)
        assert resp.liked is False


# ============================================================
# 学习小组 Schema
# ============================================================

class TestGroupSchemas:
    """小组 Schema 验证"""

    def test_group_item(self):
        group = GroupItem(
            id=1, name="发音提升组", level="B1", schedule="每天 20:00",
            tags=["发音", "口语"], member_count=15, is_joined=True,
        )
        assert group.member_count == 15
        assert group.is_joined is True

    def test_group_list(self):
        resp = GroupListResponse(groups=[
            GroupItem(id=i, name=f"小组{i}", level="B1", schedule="每天") for i in range(4)
        ])
        assert len(resp.groups) == 4

    def test_join_result(self):
        result = JoinResult(joined=True, member_count=16)
        assert result.joined is True
        assert result.member_count == 16

    def test_leave_result(self):
        result = JoinResult(joined=False, member_count=14)
        assert result.joined is False
