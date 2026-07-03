"""英语口语水平测评 — 五维度自适应 + 固定题库 + 逐题提交"""

import os
import uuid
import json
import time
import tempfile
import logging
import shutil
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.assessment import AssessmentQuestion, AssessmentRecord
from app.schemas.assessment import (
    QuestionItem,
    AssessmentStartResponse,
    AssessmentAnswerResponse,
    AssessmentSubmitResponse,
    CEFRLevel,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.audio_utils import convert_to_wav

router = APIRouter()
logger = logging.getLogger(__name__)

# ========== 常量 ==========

CEFR_NUMERIC = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0}
CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1"]
NUMERIC_CEFR = {v: k for k, v in CEFR_NUMERIC.items()}

TOTAL_QUESTIONS = 6

# 六题维度序列：按画像五维度覆盖，发音多测一次
DIMENSION_SEQUENCE = [
    "pronunciation",
    "grammar",
    "fluency",
    "vocabulary",
    "interaction",
    "pronunciation",
]

# 需要音频输入的口语维度
SPEAKING_DIMENSIONS = {"pronunciation", "fluency", "interaction"}

DIMENSION_LABELS = {
    "pronunciation": "发音",
    "fluency": "流利度",
    "grammar": "语法",
    "vocabulary": "词汇运用",
    "interaction": "互动参与",
}

DIMENSION_SUGGESTIONS = {
    "pronunciation": "建议多进行跟读练习，注意音素准确度和重音位置",
    "fluency": "建议多进行自由口语练习，减少停顿和重复，提升语速和连贯性",
    "grammar": "建议系统复习基础语法知识，重点关注时态和句型结构",
    "vocabulary": "建议每天积累新词汇，多做词汇运用练习",
    "interaction": "建议多参与对话和角色扮演练习，提升互动应对能力",
}

CEFR_THRESHOLDS = [
    (96, "C1", "高级"),
    (81, "B2", "中高级"),
    (61, "B1", "中级"),
    (41, "A2", "基础"),
    (0, "A1", "入门"),
]

# ========== 会话存储 ==========
_sessions: dict[str, dict] = {}


# ========== 工具函数 ==========

def _get_cefr(score: float, age_group: str = "大学生") -> tuple:
    from app.services.age_adaptive import get_assessment_age_offset
    offset = get_assessment_age_offset(age_group)
    adjusted = score - offset
    for threshold, level, label in CEFR_THRESHOLDS:
        if adjusted >= threshold:
            return level, label
    return "A1", "入门"


def _level_to_cefr(level: float) -> str:
    rounded = round(level)
    rounded = max(1, min(5, rounded))
    return NUMERIC_CEFR[float(rounded)]


def _adjust_level(current: float, score: float) -> float:
    delta = 0.5 if score >= 60 else -0.5
    return max(1.0, min(5.0, current + delta))


def _get_question(db: Session, dimension: str, target_cefr: str) -> AssessmentQuestion | None:
    """从题库随机抽题，优先匹配维度和难度，允许重复使用"""
    q = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.is_active == 1,
            AssessmentQuestion.dimension == dimension,
            AssessmentQuestion.difficulty == target_cefr,
        )
        .order_by(func.rand())
        .first()
    )
    if q:
        return q

    # 难度回退
    target_idx = CEFR_ORDER.index(target_cefr) if target_cefr in CEFR_ORDER else 2
    for offset in range(1, len(CEFR_ORDER)):
        for direction in (-1, 1):
            idx = target_idx + offset * direction
            if 0 <= idx < len(CEFR_ORDER):
                q = (
                    db.query(AssessmentQuestion)
                    .filter(
                        AssessmentQuestion.is_active == 1,
                        AssessmentQuestion.dimension == dimension,
                        AssessmentQuestion.difficulty == CEFR_ORDER[idx],
                    )
                    .order_by(func.rand())
                    .first()
                )
                if q:
                    return q

    # 兜底：同维度任意难度
    return (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.is_active == 1, AssessmentQuestion.dimension == dimension)
        .order_by(func.rand())
        .first()
    )


def _question_to_item(q: AssessmentQuestion) -> QuestionItem:
    return QuestionItem(
        id=q.id,
        type=q.dimension,
        difficulty=q.difficulty,
        content=q.question_text,
        options=q.options or [],
        audio_base64=None,
    )


# ========== API 端点 ==========

@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开始自适应测评 — 从固定题库抽取第一题（发音维度）。"""
    if current_user.assessment_completed:
        last_record = (
            db.query(AssessmentRecord)
            .filter(AssessmentRecord.user_id == current_user.id)
            .order_by(AssessmentRecord.created_at.desc())
            .first()
        )
        if last_record:
            days_since = (datetime.now(timezone.utc) - last_record.created_at.replace(tzinfo=timezone.utc)).days
            if days_since < 30:
                raise HTTPException(
                    status_code=429,
                    detail=f"测评完成后 30 天内不可重新测评，距离上次测评已过 {days_since} 天",
                )

    session_id = str(uuid.uuid4())
    start_cefr = current_user.level_self if current_user.level_self in CEFR_NUMERIC else "B1"

    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": CEFR_NUMERIC.get(start_cefr, 3.0),
        "dimension_scores": {d: [] for d in DIMENSION_LABELS},
        "question_order": 0,
        "start_time": time.time(),
    }

    first_dim = DIMENSION_SEQUENCE[0]
    question = _get_question(db, first_dim, start_cefr)
    if not question:
        raise HTTPException(status_code=503, detail="题库为空，无法开始测评")

    logger.info(
        f"用户 {current_user.username} 开始测评 session={session_id} "
        f"start_level={start_cefr} dim={first_dim} qid={question.id}"
    )

    return AssessmentStartResponse(
        session_id=session_id,
        question=_question_to_item(question),
        total_questions=TOTAL_QUESTIONS,
        current_difficulty=start_cefr,
    )


@router.post("/answer", response_model=AssessmentAnswerResponse)
async def answer_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    question_id: int = Form(..., description="题目 ID"),
    answer: str = Form(default="", description="选择题答案 A/B/C/D"),
    audio: UploadFile | None = File(default=None, description="口语音频"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交题目答案 — 口语题 ASR+LLM 评分，选择题比对答案。"""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评会话不存在或已过期")
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    dimension = question.dimension
    is_speaking = dimension in SPEAKING_DIMENSIONS

    audio_url = None
    transcript = ""
    score = 0.0
    is_correct = None

    if is_speaking:
        # 口语题：ASR 转写 + LLM 评分
        if audio and audio.size > 0:
            try:
                suffix = ".webm"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    content = await audio.read()
                    tmp.write(content)
                    tmp_path = tmp.name

                wav_path = convert_to_wav(tmp_path)
                asr_service = get_asr_service()
                asr_result = asr_service.transcribe(wav_path)
                transcript = asr_result.get("text", "").strip()

                if transcript:
                    target_cefr = _level_to_cefr(session["current_level"])
                    llm_service = get_llm_service()
                    score_result = await llm_service.score_speaking(
                        transcript, target_cefr, current_user.age_group,
                    )
                    score = float(score_result.get("total", 60))
                else:
                    score = 0.0

                audio_dir = f"uploads/assessment/{session_id}"
                os.makedirs(audio_dir, exist_ok=True)
                shutil.copy(tmp_path, os.path.join(audio_dir, f"q{question_id}.webm"))
                audio_url = f"/{audio_dir}/q{question_id}.webm"

                os.unlink(tmp_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

                logger.info(f"口语评分: qid={question_id} dim={dimension} score={score}")
            except Exception as e:
                logger.error(f"口语题处理失败: {e}")
                score = 60.0
                transcript = f"[处理失败: {str(e)[:100]}]"
        else:
            score = 0.0
    else:
        # 选择题：比对答案
        correct_letter = chr(64 + int(question.correct_option))
        is_correct = 1 if answer.strip().upper() == correct_letter else 0
        score = 100.0 if is_correct else 0.0

    # 记录分数
    session["dimension_scores"][dimension].append(score)
    session["question_order"] += 1
    old_level = session["current_level"]
    session["current_level"] = _adjust_level(old_level, score)

    # 写入数据库
    question_data = {
        "question_text": question.question_text,
        "dimension": dimension,
        "difficulty": question.difficulty,
        "correct_option": question.correct_option if not is_speaking else None,
        "options": question.options,
    }

    record = AssessmentRecord(
        user_id=current_user.id,
        session_id=session_id,
        question_id=question_id,
        question_type=dimension,
        user_answer=answer if not is_speaking else (transcript or ""),
        is_correct=is_correct,
        score=score,
        audio_url=audio_url,
        transcript=transcript,
        question_order=session["question_order"],
        question_data=question_data,
    )
    db.add(record)
    db.commit()

    # 检查是否完成
    next_index = session["question_order"]
    if next_index >= TOTAL_QUESTIONS:
        return AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty=_level_to_cefr(session["current_level"]),
        )

    # 下一题
    next_dim = DIMENSION_SEQUENCE[next_index]
    target_cefr = _level_to_cefr(session["current_level"])
    next_q = _get_question(db, next_dim, target_cefr)

    if not next_q:
        return AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty=target_cefr,
        )

    logger.info(
        f"测评答题: user={current_user.username} qid={question_id} dim={dimension} "
        f"score={score} level={old_level:.1f}→{session['current_level']:.1f} "
        f"next: {next_dim} qid={next_q.id}"
    )

    return AssessmentAnswerResponse(
        complete=False,
        next_question=_question_to_item(next_q),
        current_difficulty=target_cefr,
    )


@router.post("/restore")
async def restore_session(
    session_id: str = Form(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """恢复中断的测评会话。"""
    records = (
        db.query(AssessmentRecord)
        .filter(AssessmentRecord.session_id == session_id, AssessmentRecord.user_id == current_user.id)
        .order_by(AssessmentRecord.question_order)
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="测评会话不存在或无答题记录")

    dimension_scores = {d: [] for d in DIMENSION_LABELS}
    current_level = 3.0

    for rec in records:
        if rec.score is not None:
            current_level = _adjust_level(current_level, float(rec.score))
        dim = rec.question_type if rec.question_type in dimension_scores else "pronunciation"
        if rec.score is not None:
            dimension_scores[dim].append(float(rec.score))

    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": current_level,
        "dimension_scores": dimension_scores,
        "question_order": len(records),
        "start_time": time.time(),
    }

    next_index = len(records)
    if next_index >= TOTAL_QUESTIONS:
        return {"complete": True, "answered_count": len(records)}

    next_dim = DIMENSION_SEQUENCE[next_index]
    target_cefr = _level_to_cefr(current_level)
    next_q = _get_question(db, next_dim, target_cefr)

    if not next_q:
        return {"complete": True, "answered_count": len(records)}

    return {
        "complete": False,
        "answered_count": len(records),
        "next_question": _question_to_item(next_q).model_dump(),
        "current_difficulty": target_cefr,
    }


@router.post("/complete", response_model=AssessmentSubmitResponse)
async def complete_assessment(
    session_id: str = Form(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """完成测评 — 五维度评分 + 更新用户画像。"""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评会话不存在或已过期")
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 计算各维度均分
    dimension_scores = {}
    for dim, scores in session["dimension_scores"].items():
        dimension_scores[dim] = round(sum(scores) / len(scores), 1) if scores else 0.0

    # 综合分 = 五维度加权
    weights = {"pronunciation": 0.30, "fluency": 0.25, "grammar": 0.15, "vocabulary": 0.15, "interaction": 0.15}
    overall = round(sum(dimension_scores[d] * weights[d] for d in weights), 1)

    level, label = _get_cefr(overall, current_user.age_group)

    # 短板：分数最低的维度
    weak_dim = min(dimension_scores, key=dimension_scores.get)
    weakness = {
        "dimension": weak_dim,
        "score": dimension_scores[weak_dim],
        "label": DIMENSION_LABELS[weak_dim],
        "suggestion": DIMENSION_SUGGESTIONS[weak_dim],
    }

    start_time = session.get("start_time")
    duration_seconds = int(time.time() - start_time) if start_time else 0

    current_user.level_test = level
    current_user.level_final = level
    current_user.assessment_completed = 1
    db.commit()

    from app.services.profile_updater import profile_updater
    profile_updater.ingest_assessment_scores(current_user.id, dimension_scores, session_id, db)
    db.commit()

    # 逐题详情
    records = (
        db.query(AssessmentRecord)
        .filter(AssessmentRecord.session_id == session_id, AssessmentRecord.user_id == current_user.id)
        .order_by(AssessmentRecord.question_order)
        .all()
    )

    questions_detail = []
    for rec in records:
        qdata = rec.question_data if isinstance(rec.question_data, dict) else (json.loads(str(rec.question_data)) if rec.question_data else {})
        dim = qdata.get("dimension", rec.question_type) if qdata else rec.question_type
        difficulty = qdata.get("difficulty", "B1") if qdata else "B1"
        question_text = qdata.get("question_text", "") if qdata else ""
        is_speaking = dim in SPEAKING_DIMENSIONS

        correct_answer = None
        if not is_speaking and qdata:
            co = qdata.get("correct_option", 1)
            correct_answer = chr(64 + int(co)) if co else None

        questions_detail.append({
            "order": rec.question_order,
            "type": dim,
            "type_label": DIMENSION_LABELS.get(dim, dim),
            "difficulty": difficulty,
            "content": question_text[:80] + ("..." if len(question_text) > 80 else ""),
            "user_answer": rec.user_answer[:60] if rec.user_answer and not is_speaking else None,
            "correct_answer": correct_answer,
            "is_correct": bool(rec.is_correct) if rec.is_correct is not None else None,
            "score": float(rec.score) if rec.score else 0.0,
            "transcript": rec.transcript[:100] if rec.transcript and is_speaking else None,
        })

    del _sessions[session_id]

    logger.info(
        f"用户 {current_user.username} 完成测评: overall={overall} level={level} "
        f"dims={dimension_scores} duration={duration_seconds}s"
    )

    return AssessmentSubmitResponse(
        overall=overall,
        cefr_level=CEFRLevel(level=level, label=label),
        dimension_scores=dimension_scores,
        weakness=weakness,
        duration=duration_seconds,
        questions_detail=questions_detail,
    )


# ========== 旧端点（兼容） ==========

@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    session_id: str = Form(...),
    answers: str = Form(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """[已废弃] 批量提交，直接跳到完成。"""
    logger.warning(f"用户 {current_user.username} 使用了已废弃的批量提交端点")
    return await complete_assessment(session_id, current_user, db)
