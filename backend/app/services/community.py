"""社区服务 — 语音挑战 / 话题讨论 / 学习小组"""

import logging
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.community import (
    VoiceChallenge,
    ChallengeSubmission,
    DiscussionPost,
    PostComment,
    PostLike,
    StudyGroup,
    GroupMember,
)
from app.models.user import UserProfile

logger = logging.getLogger(__name__)


class CommunityService:
    """社区服务"""

    # ============================================================
    # 语音挑战
    # ============================================================

    def get_active_challenges(self, db: Session) -> List[Dict]:
        """获取进行中的挑战列表"""
        challenges = (
            db.query(VoiceChallenge)
            .filter(VoiceChallenge.is_active == True)
            .order_by(VoiceChallenge.created_at.desc())
            .all()
        )
        result = []
        for c in challenges:
            participants = (
                db.query(func.count(ChallengeSubmission.id))
                .filter(ChallengeSubmission.challenge_id == c.id)
                .scalar()
            ) or 0
            result.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "sample_text": c.sample_text,
                "deadline": c.deadline.isoformat() if c.deadline else "",
                "is_active": c.is_active,
                "participants_count": participants,
                "created_at": c.created_at.isoformat() if c.created_at else "",
            })
        return result

    def submit_challenge(
        self, user_id: int, challenge_id: int, audio_url: str, db: Session
    ) -> Dict:
        """提交挑战录音并评分"""
        # 检查挑战是否存在
        challenge = db.query(VoiceChallenge).filter(VoiceChallenge.id == challenge_id).first()
        if not challenge:
            raise ValueError("挑战不存在")

        # 语音评分（复用发音评测服务 — 同步版本）
        pronunciation_score = None
        fluency_score = None
        total_score = None
        try:
            from app.services.pronunciation import get_pronunciation_service
            pron_service = get_pronunciation_service()
            score_result = pron_service.score(audio_url, challenge.sample_text, "sentence")
            if score_result:
                total_score = int(score_result.get("overall", 0))
                dimensions = score_result.get("dimensions", [])
                for d in dimensions:
                    label = d.get("label", "")
                    if "音素" in label:
                        pronunciation_score = int(d["score"])
                    if "节奏" in label:
                        fluency_score = int(d["score"])
                if pronunciation_score is None:
                    pronunciation_score = total_score
                if fluency_score is None:
                    fluency_score = total_score
        except Exception as e:
            logger.warning(f"挑战评分失败: {e}")

        submission = ChallengeSubmission(
            user_id=user_id,
            challenge_id=challenge_id,
            audio_url=audio_url,
            pronunciation_score=pronunciation_score,
            fluency_score=fluency_score,
            total_score=total_score,
        )
        db.add(submission)
        db.flush()

        # 获取排名
        better_count = (
            db.query(func.count(ChallengeSubmission.id))
            .filter(
                ChallengeSubmission.challenge_id == challenge_id,
                ChallengeSubmission.total_score > total_score,
            )
            .scalar()
        ) or 0
        rank = better_count + 1

        return {
            "submission": {
                "id": submission.id,
                "user_id": submission.user_id,
                "username": "",
                "challenge_id": submission.challenge_id,
                "audio_url": submission.audio_url,
                "pronunciation_score": submission.pronunciation_score,
                "fluency_score": submission.fluency_score,
                "total_score": submission.total_score,
                "created_at": submission.created_at.isoformat() if submission.created_at else "",
            },
            "rank": rank,
        }

    def get_leaderboard(self, challenge_id: int, db: Session) -> Dict:
        """获取挑战排行榜"""
        submissions = (
            db.query(ChallengeSubmission)
            .filter(ChallengeSubmission.challenge_id == challenge_id)
            .order_by(desc(ChallengeSubmission.total_score))
            .limit(20)
            .all()
        )
        leaderboard = []
        for i, s in enumerate(submissions):
            user = db.query(UserProfile).filter(UserProfile.id == s.user_id).first()
            leaderboard.append({
                "rank": i + 1,
                "user_id": s.user_id,
                "username": user.username if user else "未知",
                "total_score": s.total_score,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            })
        return {
            "challenge_id": challenge_id,
            "leaderboard": leaderboard,
        }

    # ============================================================
    # 话题讨论
    # ============================================================

    def get_posts(self, user_id: int, db: Session) -> List[Dict]:
        """获取帖子列表"""
        posts = (
            db.query(DiscussionPost)
            .order_by(DiscussionPost.created_at.desc())
            .limit(50)
            .all()
        )
        result = []
        for p in posts:
            user = db.query(UserProfile).filter(UserProfile.id == p.user_id).first()
            # 检查当前用户是否已点赞
            liked = (
                db.query(PostLike)
                .filter(
                    PostLike.post_id == p.id,
                    PostLike.user_id == user_id,
                )
                .first()
                is not None
            )
            result.append({
                "id": p.id,
                "user_id": p.user_id,
                "username": user.username if user else "未知",
                "avatar": (user.username or "?")[0].upper() if user else "?",
                "topic": p.topic,
                "content": p.content,
                "likes_count": p.likes_count,
                "comments_count": p.comments_count,
                "is_liked": liked,
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "updated_at": p.updated_at.isoformat() if p.updated_at else "",
            })
        return result

    def create_post(self, user_id: int, topic: str, content: str, db: Session) -> Dict:
        """发帖"""
        post = DiscussionPost(
            user_id=user_id,
            topic=topic,
            content=content,
        )
        db.add(post)
        db.flush()
        return {
            "id": post.id,
            "user_id": post.user_id,
            "username": "",
            "avatar": "",
            "topic": post.topic,
            "content": post.content,
            "likes_count": 0,
            "comments_count": 0,
            "is_liked": False,
            "created_at": post.created_at.isoformat() if post.created_at else "",
            "updated_at": post.updated_at.isoformat() if post.updated_at else "",
        }

    def toggle_like(self, user_id: int, post_id: int, db: Session) -> Dict:
        """切换点赞状态"""
        existing = (
            db.query(PostLike)
            .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
            .first()
        )
        post = db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
        if not post:
            raise ValueError("帖子不存在")

        if existing:
            db.delete(existing)
            post.likes_count = max(0, post.likes_count - 1)
            liked = False
        else:
            db.add(PostLike(post_id=post_id, user_id=user_id))
            post.likes_count += 1
            liked = True
        db.flush()
        return {"liked": liked, "likes_count": post.likes_count}

    def get_comments(self, post_id: int, db: Session) -> List[Dict]:
        """获取评论列表"""
        comments = (
            db.query(PostComment)
            .filter(PostComment.post_id == post_id)
            .order_by(PostComment.created_at.asc())
            .all()
        )
        result = []
        for c in comments:
            user = db.query(UserProfile).filter(UserProfile.id == c.user_id).first()
            result.append({
                "id": c.id,
                "user_id": c.user_id,
                "username": user.username if user else "未知",
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else "",
            })
        return result

    def add_comment(self, user_id: int, post_id: int, content: str, db: Session) -> Dict:
        """发表评论"""
        post = db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
        if not post:
            raise ValueError("帖子不存在")

        comment = PostComment(
            post_id=post_id,
            user_id=user_id,
            content=content,
        )
        db.add(comment)
        post.comments_count += 1
        db.flush()
        return {
            "id": comment.id,
            "user_id": comment.user_id,
            "username": "",
            "content": comment.content,
            "created_at": comment.created_at.isoformat() if comment.created_at else "",
        }

    # ============================================================
    # 学习小组
    # ============================================================

    def get_groups(self, user_id: int, db: Session) -> List[Dict]:
        """获取小组列表"""
        groups = (
            db.query(StudyGroup)
            .filter(StudyGroup.is_archived == False)
            .order_by(StudyGroup.member_count.desc())
            .all()
        )
        # 查询用户已加入的小组
        joined_ids = set()
        if user_id:
            memberships = (
                db.query(GroupMember.group_id)
                .filter(GroupMember.user_id == user_id)
                .all()
            )
            joined_ids = {m[0] for m in memberships}

        result = []
        for g in groups:
            tags = [t.strip() for t in g.tags.split(",") if t.strip()] if g.tags else []
            result.append({
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "level": g.level_range or "",
                "schedule": g.schedule or "",
                "tags": tags,
                "member_count": g.member_count,
                "is_joined": g.id in joined_ids,
                "created_at": g.created_at.isoformat() if g.created_at else "",
            })
        return result

    def toggle_group(self, user_id: int, group_id: int, db: Session) -> Dict:
        """加入/退出小组"""
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        if not group:
            raise ValueError("小组不存在")

        existing = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )

        if existing:
            db.delete(existing)
            group.member_count = max(0, group.member_count - 1)
            joined = False
        else:
            db.add(GroupMember(group_id=group_id, user_id=user_id))
            group.member_count += 1
            joined = True
        db.flush()
        return {"joined": joined, "member_count": group.member_count}


# 单例
community_service = CommunityService()