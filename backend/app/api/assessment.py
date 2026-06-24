"""英语水平测评 API 路由"""

import os
import uuid
import tempfile
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, LEARNING_GOAL_MAP
from app.models.user import UserProfile
from app.models.assessment import AssessmentQuestion, AssessmentRecord
from app.schemas.assessment import (
    QuestionItem,
    AssessmentStartResponse,
    AnswerItem,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    DimensionScore,
    CEFRLevel,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

# CEFR 定级阈值
CEFR_THRESHOLDS = [
    (96, "C2", "精通"),
    (81, "C1", "高级"),
    (61, "B2", "中高级"),
    (41, "B1", "中级"),
    (21, "A2", "基础"),
    (0, "A1", "入门"),
]

DIMENSION_LABELS = {
    "listening": "听力理解",
    "speaking": "口语表达",
    "reading": "阅读理解",
    "grammar": "语法选择",
}

SUGGESTIONS = {
    "listening": "建议每天听15分钟英语播客或新闻，逐步提升听力理解能力",
    "speaking": "建议多进行口语练习，可以先从简单的自我介绍和日常话题开始",
    "reading": "建议每天阅读一篇英语短文，注意积累词汇和理解文章结构",
    "grammar": "建议系统复习基础语法知识，重点关注时态和句型结构",
}


def _get_cefr(score: float) -> tuple:
    """根据分数返回 CEFR 等级"""
    for threshold, level, label in CEFR_THRESHOLDS:
        if score >= threshold:
            return level, label
    return "A1", "入门"


@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始测评 — 返回 10 道题目和会话 ID。
    从题库中按维度均匀抽取（2-3题/维度），混合难度。
    """
    session_id = str(uuid.uuid4())

    # 按维度各取 2-3 题，共 10 题
    dimensions = ["listening", "speaking", "reading", "grammar"]
    questions = []

    for i, dim in enumerate(dimensions):
        # 前两个维度取 3 题，后两个取 2 题
        limit = 3 if i < 2 else 2
        dim_questions = (
            db.query(AssessmentQuestion)
            .filter(
                AssessmentQuestion.dimension == dim,
                AssessmentQuestion.is_active == 1,
            )
            .order_by(AssessmentQuestion.id)
            .limit(limit)
            .all()
        )
        for q in dim_questions:
            questions.append(
                QuestionItem(
                    id=q.id,
                    type=q.dimension,
                    difficulty=q.difficulty,
                    content=q.question_text,
                    options=q.options if q.options else [],
                )
            )

    # 如果题库不足，用已有题目补足
    if len(questions) < 10:
        logger.warning(f"题库不足，仅有 {len(questions)} 题")

    logger.info(f"用户 {current_user.username} 开始测评，session={session_id}")

    return AssessmentStartResponse(
        session_id=session_id,
        questions=questions[:10],
    )


@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    answers: str = Form(..., description="JSON 字符串：[{question_id, answer}, ...]"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交测评答案 — 判分并返回 CEFR 等级。
    接收 JSON 格式的答案列表，口语题目前使用默认评分（无音频时不调用 ASR）。
    """
    import json

    try:
        answer_list = json.loads(answers)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="答案格式错误")

    # 维度累计分数
    dimension_totals = {"listening": [], "speaking": [], "reading": [], "grammar": []}
    record_order = 0

    for item in answer_list:
        record_order += 1
        question_id = item.get("question_id")
        user_answer = item.get("answer")

        question = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.id == question_id
        ).first()

        if not question:
            continue

        is_speaking = question.dimension == "speaking"
        question_type = "speaking" if is_speaking else "multiple_choice"

        if is_speaking:
            # 口语题：默认给 60 分（无音频时），实际应通过 ASR+LLM 评分
            score = 60.0
            is_correct = None
        else:
            # 客观题：比对正确选项
            # 选项格式：["A. xxx", "B. xxx", "C. xxx", "D. xxx"]
            correct_letter = chr(64 + question.correct_option)  # 1→A, 2→B, ...
            is_correct = 1 if user_answer == correct_letter else 0
            score = 100.0 if is_correct else 0.0

        dimension_totals[question.dimension].append(score)

        # 写入记录
        record = AssessmentRecord(
            user_id=current_user.id,
            session_id=session_id,
            question_id=question_id,
            question_type=question_type,
            user_answer=user_answer,
            is_correct=is_correct,
            score=score,
            question_order=record_order,
        )
        db.add(record)

    # 计算四维均分
    dimension_scores = {}
    for dim, scores in dimension_totals.items():
        if scores:
            dimension_scores[dim] = round(sum(scores) / len(scores), 1)
        else:
            dimension_scores[dim] = 0.0

    # 综合分 = 四维均分
    overall = round(sum(dimension_scores.values()) / 4, 1)

    # CEFR 定级
    level, label = _get_cefr(overall)

    # 短板维度
    weakness_dim = min(dimension_scores, key=dimension_scores.get)
    weakness = {
        "dimension": weakness_dim,
        "score": dimension_scores[weakness_dim],
        "label": DIMENSION_LABELS.get(weakness_dim, weakness_dim),
        "suggestion": SUGGESTIONS.get(weakness_dim, ""),
    }

    # 更新用户画像
    current_user.level_test = level
    current_user.level_final = level
    current_user.assessment_completed = 1

    db.commit()

    logger.info(
        f"用户 {current_user.username} 完成测评: overall={overall}, level={level}"
    )

    return AssessmentSubmitResponse(
        overall=overall,
        cefr_level=CEFRLevel(level=level, label=label),
        dimension_scores=dimension_scores,
        weakness=weakness,
        duration=0,
    )