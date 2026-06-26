"""英语水平测评 API 路由 — 自适应难度 + 逐题提交 + 会话持久化"""

import os
import uuid
import json
import tempfile
import logging
import subprocess
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

CEFR_NUMERIC = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}
NUMERIC_CEFR = {v: k for k, v in CEFR_NUMERIC.items()}

# 维度序列：10 题 = 听力3 + 口语2 + 阅读3 + 语法2
DIMENSION_SEQUENCE = [
    "listening", "reading", "grammar", "speaking",
    "listening", "reading", "grammar", "reading",
    "listening", "speaking",
]

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

# ========== 会话存储 ==========
# 注意：正式环境应使用数据库存储，当前使用内存字典 + DB 记录双写
_sessions: dict[str, dict] = {}

# 全对/全错追加题阈值
BONUS_THRESHOLD_CORRECT = 10   # 全对（10 题全答对）追加 C2 确认题
BONUS_THRESHOLD_WRONG = 0      # 全错（10 题全答错）追加 A1 兜底题

# ========== 工具函数 ==========

def _get_cefr(score: float) -> tuple:
    for threshold, level, label in CEFR_THRESHOLDS:
        if score >= threshold:
            return level, label
    return "A1", "入门"


def _level_to_cefr(level: float) -> str:
    """将数值等级四舍五入到最近的 CEFR 等级"""
    rounded = round(level)
    rounded = max(1, min(6, rounded))
    return NUMERIC_CEFR[float(rounded)]


def _adjust_level(current: float, score: float) -> float:
    """自适应难度调整：得分 ≥ 60 升 0.5 级，< 60 降 0.5 级"""
    delta = 0.5 if score >= 60 else -0.5
    return max(1.0, min(6.0, current + delta))


def _select_question(db: Session, dimension: str, target_cefr: str, exclude_ids: set) -> AssessmentQuestion | None:
    """按维度和目标 CEFR 等级选一道题，排除已答题目"""
    # 优先匹配目标 CEFR 等级
    q = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.dimension == dimension,
            AssessmentQuestion.difficulty == target_cefr,
            AssessmentQuestion.is_active == 1,
            ~AssessmentQuestion.id.in_(exclude_ids) if exclude_ids else True,
        )
        .order_by(func.rand())
        .first()
    )
    if q:
        return q

    # 如果目标等级无题，放宽到相邻等级
    q = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.dimension == dimension,
            AssessmentQuestion.is_active == 1,
            ~AssessmentQuestion.id.in_(exclude_ids) if exclude_ids else True,
        )
        .order_by(func.rand())
        .first()
    )
    return q


# ========== API 端点 ==========

@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始自适应测评 — 返回第一题。
    起始难度基于用户自评等级，默认 B1。
    限制：30 天内只能重新测评一次。
    """
    # 30 天重测评限制
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

    # 起始难度：自评等级 → CEFR，默认 B1
    start_cefr = current_user.level_self if current_user.level_self in CEFR_NUMERIC else "B1"
    current_level = CEFR_NUMERIC.get(start_cefr, 3.0)

    # 第一题：维度序列第一个 + 起始难度
    first_dim = DIMENSION_SEQUENCE[0]
    first_question = _select_question(db, first_dim, start_cefr, set())

    if not first_question:
        raise HTTPException(status_code=500, detail="题库不足，请联系管理员")

    # 初始化会话
    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": current_level,
        "dimension_totals": {"listening": [], "speaking": [], "reading": [], "grammar": []},
        "question_order": 0,
        "answered_ids": set(),
        "start_time": None,
        "bonus_added": False,
    }

    question = QuestionItem(
        id=first_question.id,
        type=first_question.dimension,
        difficulty=first_question.difficulty,
        content=first_question.question_text,
        options=first_question.options if first_question.options else [],
    )

    logger.info(
        f"用户 {current_user.username} 开始自适应测评 session={session_id} "
        f"start_level={start_cefr}"
    )

    return AssessmentStartResponse(
        session_id=session_id,
        question=question,
        total_questions=len(DIMENSION_SEQUENCE),
        current_difficulty=start_cefr,
    )


@router.post("/answer", response_model=AssessmentAnswerResponse)
async def answer_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    question_id: int = Form(..., description="题目 ID"),
    answer: str = Form(default="", description="客观题：选项字母 A/B/C/D；口语题：空字符串"),
    audio: UploadFile | None = File(default=None, description="口语音频文件"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交单题答案 — 判分 + 自适应难度调整 + 返回下一题。
    口语题携带音频文件，后端执行 ASR + LLM 评分。
    """
    # 验证会话
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评会话不存在或已过期")
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 记录开始时间
    if session["start_time"] is None:
        session["start_time"] = None  # 保留字段

    # 验证题目
    question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    is_speaking = question.dimension == "speaking"
    question_type = "speaking" if is_speaking else "multiple_choice"

    # 判分
    audio_url = None
    transcript = None

    if is_speaking:
        # 口语题：ASR + LLM 评分
        if audio and audio.size > 0:
            try:
                # 保存音频到临时文件
                suffix = ".webm"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    content = await audio.read()
                    tmp.write(content)
                    tmp_path = tmp.name

                # 转码为 WAV
                wav_path = convert_to_wav(tmp_path)

                # WhisperX 转写
                asr_service = get_asr_service()
                asr_result = asr_service.transcribe(wav_path)
                transcript = asr_result.get("text", "").strip()

                # LLM 四维评分
                if transcript:
                    target_cefr = _level_to_cefr(session["current_level"])
                    llm_service = get_llm_service()
                    score_result = await llm_service.score_speaking(transcript, target_cefr)
                    score = float(score_result.get("total", 60))
                else:
                    score = 0.0
                    transcript = ""

                # 保存音频到持久化目录
                audio_dir = f"uploads/assessment/{session_id}"
                os.makedirs(audio_dir, exist_ok=True)
                audio_filename = f"q{question_id}.webm"
                audio_path = os.path.join(audio_dir, audio_filename)
                shutil.copy(tmp_path, audio_path)
                audio_url = f"/{audio_path}"

                # 清理临时文件
                os.unlink(tmp_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

                logger.info(f"口语题评分: qid={question_id}, transcript={transcript[:50]}..., score={score}")

            except Exception as e:
                logger.error(f"口语题处理失败: {e}")
                score = 60.0
                transcript = f"[ASR 失败: {str(e)[:100]}]"
        else:
            # 无音频 → 跳过/未作答
            score = 0.0
            transcript = ""
            logger.info(f"口语题无音频: qid={question_id}")

        is_correct = None
    else:
        # 客观题：比对正确选项
        correct_letter = chr(64 + question.correct_option)  # 1→A, 2→B, ...
        is_correct = 1 if answer.strip().upper() == correct_letter else 0
        score = 100.0 if is_correct else 0.0

    # 累计维度分数
    session["dimension_totals"][question.dimension].append(score)
    session["question_order"] += 1
    session["answered_ids"].add(question_id)

    # 自适应难度调整
    old_level = session["current_level"]
    session["current_level"] = _adjust_level(old_level, score)

    # 写入记录
    record = AssessmentRecord(
        user_id=current_user.id,
        session_id=session_id,
        question_id=question_id,
        question_type=question_type,
        user_answer=answer if not is_speaking else (transcript or ""),
        is_correct=is_correct,
        score=score,
        audio_url=audio_url,
        transcript=transcript,
        question_order=session["question_order"],
    )
    db.add(record)
    db.commit()

    # 检查是否还有下一题
    next_index = session["question_order"]

    # 全对/全错追加题逻辑
    base_questions = len(DIMENSION_SEQUENCE)
    if next_index == base_questions:
        # 基础 10 题答完，检查是否需要追加
        all_scores = []
        for dim_scores in session["dimension_totals"].values():
            all_scores.extend(dim_scores)

        if len(all_scores) >= base_questions:
            correct_count = sum(1 for s in all_scores if s >= 60)

            if correct_count >= BONUS_THRESHOLD_CORRECT and not session.get("bonus_added"):
                # 全对 → 追加 1 题 C2 确认题
                bonus_q = _select_question(db, "speaking", "C2", session["answered_ids"])
                if bonus_q:
                    session["bonus_added"] = True
                    bonus_item = QuestionItem(
                        id=bonus_q.id,
                        type=bonus_q.dimension,
                        difficulty=bonus_q.difficulty,
                        content=bonus_q.question_text,
                        options=bonus_q.options if bonus_q.options else [],
                    )
                    logger.info(f"全对追加 C2 确认题: session={session_id}")
                    return AssessmentAnswerResponse(
                        complete=False,
                        next_question=bonus_item,
                        current_difficulty="C2",
                    )

            elif correct_count <= BONUS_THRESHOLD_WRONG and not session.get("bonus_added"):
                # 全错 → 追加 1 题 A1 兜底题
                bonus_q = _select_question(db, "listening", "A1", session["answered_ids"])
                if bonus_q:
                    session["bonus_added"] = True
                    bonus_item = QuestionItem(
                        id=bonus_q.id,
                        type=bonus_q.dimension,
                        difficulty=bonus_q.difficulty,
                        content=bonus_q.question_text,
                        options=bonus_q.options if bonus_q.options else [],
                    )
                    logger.info(f"全错追加 A1 兜底题: session={session_id}")
                    return AssessmentAnswerResponse(
                        complete=False,
                        next_question=bonus_item,
                        current_difficulty="A1",
                    )

    if next_index >= base_questions and (not session.get("bonus_added") or next_index > base_questions):
        # 全部完成（含追加题）
        return AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty=_level_to_cefr(session["current_level"]),
        )

    # 选下一题
    next_dim = DIMENSION_SEQUENCE[next_index]
    target_cefr = _level_to_cefr(session["current_level"])
    next_q = _select_question(db, next_dim, target_cefr, session["answered_ids"])

    if not next_q:
        # 题库不足，直接结束
        logger.warning(f"题库不足，session={session_id} 在第 {next_index + 1} 题提前结束")
        return AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty=target_cefr,
        )

    next_question = QuestionItem(
        id=next_q.id,
        type=next_q.dimension,
        difficulty=next_q.difficulty,
        content=next_q.question_text,
        options=next_q.options if next_q.options else [],
    )

    logger.info(
        f"测评答题: user={current_user.username}, qid={question_id}, "
        f"score={score}, level={old_level:.1f}→{session['current_level']:.1f}, "
        f"next_dim={next_dim}"
    )

    return AssessmentAnswerResponse(
        complete=False,
        next_question=next_question,
        current_difficulty=target_cefr,
    )


@router.post("/restore")
async def restore_session(
    session_id: str = Form(..., description="测评会话 UUID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    恢复测评会话 — 从数据库记录重建中断的会话。
    前端刷新页面后调用此接口恢复进度。
    """
    # 查询该会话的所有记录
    records = (
        db.query(AssessmentRecord)
        .filter(
            AssessmentRecord.session_id == session_id,
            AssessmentRecord.user_id == current_user.id,
        )
        .order_by(AssessmentRecord.question_order)
        .all()
    )

    if not records:
        raise HTTPException(status_code=404, detail="测评会话不存在或无答题记录")

    # 重建会话状态
    dimension_totals = {"listening": [], "speaking": [], "reading": [], "grammar": []}
    answered_ids = set()
    current_level = 3.0  # 默认 B1

    for rec in records:
        answered_ids.add(rec.question_id)
        question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == rec.question_id).first()
        if question and rec.score is not None:
            dimension_totals[question.dimension].append(float(rec.score))
            # 反推当前难度
            current_level = _adjust_level(current_level, float(rec.score))

    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": current_level,
        "dimension_totals": dimension_totals,
        "question_order": len(records),
        "answered_ids": answered_ids,
        "start_time": None,
        "bonus_added": len(records) > len(DIMENSION_SEQUENCE),
    }

    # 选下一题
    next_index = len(records)
    if next_index >= len(DIMENSION_SEQUENCE):
        return {"complete": True, "answered_count": len(records)}

    next_dim = DIMENSION_SEQUENCE[next_index]
    target_cefr = _level_to_cefr(current_level)
    next_q = _select_question(db, next_dim, target_cefr, answered_ids)

    if not next_q:
        return {"complete": True, "answered_count": len(records)}

    next_question = QuestionItem(
        id=next_q.id,
        type=next_q.dimension,
        difficulty=next_q.difficulty,
        content=next_q.question_text,
        options=next_q.options if next_q.options else [],
    )

    return {
        "complete": False,
        "answered_count": len(records),
        "next_question": next_question.model_dump(),
        "current_difficulty": target_cefr,
    }


@router.post("/complete", response_model=AssessmentSubmitResponse)
async def complete_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    完成测评 — 计算最终评分并更新用户画像。
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评会话不存在或已过期")
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 计算四维均分
    dimension_scores = {}
    for dim, scores in session["dimension_totals"].items():
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

    # 清理会话
    del _sessions[session_id]

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


# ========== 保留旧端点（兼容） ==========

@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    answers: str = Form(..., description="JSON 字符串：[{question_id, answer}, ...]"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    [已废弃] 批量提交测评答案。
    建议使用逐题提交：POST /answer → POST /complete。
    """
    logger.warning(f"用户 {current_user.username} 使用了已废弃的批量提交端点")

    try:
        answer_list = json.loads(answers)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="答案格式错误")

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
            score = 60.0
            is_correct = None
        else:
            correct_letter = chr(64 + question.correct_option)
            is_correct = 1 if user_answer == correct_letter else 0
            score = 100.0 if is_correct else 0.0

        dimension_totals[question.dimension].append(score)

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

    dimension_scores = {}
    for dim, scores in dimension_totals.items():
        if scores:
            dimension_scores[dim] = round(sum(scores) / len(scores), 1)
        else:
            dimension_scores[dim] = 0.0

    overall = round(sum(dimension_scores.values()) / 4, 1)
    level, label = _get_cefr(overall)

    weakness_dim = min(dimension_scores, key=dimension_scores.get)
    weakness = {
        "dimension": weakness_dim,
        "score": dimension_scores[weakness_dim],
        "label": DIMENSION_LABELS.get(weakness_dim, weakness_dim),
        "suggestion": SUGGESTIONS.get(weakness_dim, ""),
    }

    current_user.level_test = level
    current_user.level_final = level
    current_user.assessment_completed = 1
    db.commit()

    return AssessmentSubmitResponse(
        overall=overall,
        cefr_level=CEFRLevel(level=level, label=label),
        dimension_scores=dimension_scores,
        weakness=weakness,
        duration=0,
    )