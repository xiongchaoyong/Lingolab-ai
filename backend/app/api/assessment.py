"""英语水平测评 API 路由 — 自适应难度 + LLM 动态出题 + 逐题提交 + 会话持久化"""

import os
import uuid
import json
import time
import base64
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
    QuestionResultItem,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.audio_utils import convert_to_wav
from app.services.tts import synthesize_speech

router = APIRouter()
logger = logging.getLogger(__name__)

# ========== 常量 ==========

CEFR_NUMERIC = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}
NUMERIC_CEFR = {v: k for k, v in CEFR_NUMERIC.items()}

# 基础维度序列（前7题固定覆盖四维，后3题自适应弱项）
BASE_DIMENSION_SEQUENCE = [
    "listening", "reading", "grammar",
    "listening", "speaking", "reading",
    "grammar",
]
TOTAL_QUESTIONS = 10

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
_sessions: dict[str, dict] = {}

# 全对/全错追加题阈值
BONUS_THRESHOLD_CORRECT = 9    # ≥9 题全对追加 C2 确认题
BONUS_THRESHOLD_WRONG = 1      # ≤1 题答对追加 A1 兜底题

# ========== 工具函数 ==========

# 动态题目 ID 计数器（用负值避免与 DB 主键冲突）
_dynamic_id_counter = 0


def _next_dynamic_id() -> int:
    global _dynamic_id_counter
    _dynamic_id_counter -= 1
    return _dynamic_id_counter


def _get_cefr(score: float, age_group: str = "大学生") -> tuple:
    """根据分数返回 CEFR 等级，考虑年龄段偏移"""
    from app.services.age_adaptive import get_assessment_age_offset
    offset = get_assessment_age_offset(age_group)
    adjusted = score - offset
    for threshold, level, label in CEFR_THRESHOLDS:
        if adjusted >= threshold:
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


def _get_weak_dimension(session: dict) -> str | None:
    """分析当前会话中用户的弱项维度"""
    totals = session.get("dimension_totals", {})
    if not totals:
        return None
    avg_scores = {}
    for dim, scores in totals.items():
        if scores:
            avg_scores[dim] = sum(scores) / len(scores)
    if not avg_scores:
        return None
    # 返回平均分最低的维度
    return min(avg_scores, key=avg_scores.get)


def _pick_next_dimension(session: dict) -> str:
    """
    自适应选题维度：前7题固定覆盖，后3题聚焦弱项
    """
    answered_count = session.get("question_order", 0)
    if answered_count < len(BASE_DIMENSION_SEQUENCE):
        return BASE_DIMENSION_SEQUENCE[answered_count]
    # 后3题：分析弱项动态决定
    weak = _get_weak_dimension(session)
    if weak:
        # 弱项维度多出现一次
        remaining_slots = TOTAL_QUESTIONS - answered_count
        all_dims = ["listening", "reading", "grammar", "speaking"]
        # 弱项占 60%，其他轮流
        if answered_count % 5 in (0, 2) and remaining_slots > 1:
            return weak
        return all_dims[answered_count % 4]
    return BASE_DIMENSION_SEQUENCE[0]  # fallback


async def _generate_question(
    db: Session,
    dimension: str,
    cefr_level: str,
    session: dict,
    age_group: str,
) -> tuple[dict, str | None]:
    """
    LLM 动态生成题目 + 听力题生成 TTS 音频

    Returns:
        (question_dict, audio_base64 | None)
    """
    llm_service = get_llm_service()

    # 构建上下文
    prev_qs = []
    for qid, qdata in session.get("generated_questions", {}).items():
        prev_qs.append({
            "dimension": qdata.get("dimension", ""),
            "content": qdata.get("question_text", "")[:60],
        })

    context = {
        "previous_questions": prev_qs,
        "consecutive_correct": session.get("consecutive_correct", 0),
        "consecutive_wrong": session.get("consecutive_wrong", 0),
        "weak_dimension": _get_weak_dimension(session),
    }

    result = await llm_service.generate_assessment_question(
        dimension=dimension,
        cefr_level=cefr_level,
        context=context,
        age_group=age_group,
    )

    # 听力题：同步生成 TTS 音频
    audio_base64 = None
    if dimension == "listening":
        try:
            question_text = result.get("question_text", "")
            # 提取对话/独白部分（去掉 Question: 行）
            audio_text = question_text.split("Question:")[0].strip() if "Question:" in question_text else question_text
            if audio_text:
                audio_bytes = await synthesize_speech(audio_text, voice="en-US-JennyNeural")
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                logger.info(f"听力题 TTS 生成成功: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.warning(f"听力题 TTS 生成失败（题目仍可用）: {e}")

    return result, audio_base64


# ========== API 端点 ==========

@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始自适应测评 — LLM 动态生成第一题。
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

    # 初始化会话
    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": current_level,
        "dimension_totals": {"listening": [], "speaking": [], "reading": [], "grammar": []},
        "question_order": 0,
        "answered_ids": set(),
        "generated_questions": {},
        "consecutive_correct": 0,
        "consecutive_wrong": 0,
        "start_time": time.time(),
        "bonus_added": False,
    }

    # LLM 动态生成第一题
    first_dim = _pick_next_dimension(_sessions[session_id])
    qdata, audio_b64 = await _generate_question(
        db, first_dim, start_cefr, _sessions[session_id], current_user.age_group,
    )
    qid = _next_dynamic_id()
    _sessions[session_id]["generated_questions"][qid] = qdata

    question = QuestionItem(
        id=qid,
        type=first_dim,
        difficulty=start_cefr,
        content=qdata["question_text"],
        options=qdata.get("options", []),
        audio_base64=audio_b64,
    )

    logger.info(
        f"用户 {current_user.username} 开始动态自适应测评 session={session_id} "
        f"start_level={start_cefr}"
    )

    return AssessmentStartResponse(
        session_id=session_id,
        question=question,
        total_questions=TOTAL_QUESTIONS,
        current_difficulty=start_cefr,
    )


@router.post("/answer", response_model=AssessmentAnswerResponse)
async def answer_assessment(
    session_id: str = Form(..., description="测评会话 UUID"),
    question_id: int = Form(..., description="题目 ID（动态题为负值）"),
    answer: str = Form(default="", description="客观题：选项字母 A/B/C/D；口语题：空字符串"),
    audio: UploadFile | None = File(default=None, description="口语音频文件"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交单题答案 — 判分 + LLM 动态生成下一题 + 自适应难度调整。
    口语题携带音频文件，后端执行 ASR + LLM 评分。
    客观题（动态生成）正确答案从会话中读取。
    """
    # 验证会话
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评会话不存在或已过期")
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 获取题目数据（动态生成或 DB）
    qdata = session.get("generated_questions", {}).get(question_id)
    if qdata:
        # 动态生成的题目
        dimension = qdata.get("dimension", "grammar")
        correct_option = qdata.get("correct_option", 1)
    else:
        # DB 题库题目（兼容旧逻辑）
        question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")
        dimension = question.dimension
        correct_option = question.correct_option

    is_speaking = dimension == "speaking"
    question_type = "speaking" if is_speaking else "multiple_choice"

    # 判分
    audio_url = None
    transcript = None

    if is_speaking:
        # 口语题：ASR + LLM 评分
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
                    transcript = ""

                audio_dir = f"uploads/assessment/{session_id}"
                os.makedirs(audio_dir, exist_ok=True)
                audio_filename = f"q{question_id}.webm"
                audio_path = os.path.join(audio_dir, audio_filename)
                shutil.copy(tmp_path, audio_path)
                audio_url = f"/{audio_path}"

                os.unlink(tmp_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

                logger.info(f"口语题评分: qid={question_id}, transcript={transcript[:50]}..., score={score}")

            except Exception as e:
                logger.error(f"口语题处理失败: {e}")
                score = 60.0
                transcript = f"[ASR 失败: {str(e)[:100]}]"
        else:
            score = 0.0
            transcript = ""
            logger.info(f"口语题无音频: qid={question_id}")

        is_correct = None
    else:
        # 客观题：比对正确选项
        correct_letter = chr(64 + int(correct_option))  # 1→A, 2→B, ...
        is_correct = 1 if answer.strip().upper() == correct_letter else 0
        score = 100.0 if is_correct else 0.0

    # 更新连续答对/错计数
    if is_correct == 1:
        session["consecutive_correct"] = session.get("consecutive_correct", 0) + 1
        session["consecutive_wrong"] = 0
    elif is_correct == 0:
        session["consecutive_wrong"] = session.get("consecutive_wrong", 0) + 1
        session["consecutive_correct"] = 0

    # 累计维度分数
    session["dimension_totals"][dimension].append(score)
    session["question_order"] += 1
    session["answered_ids"].add(question_id)

    # 自适应难度调整
    old_level = session["current_level"]
    session["current_level"] = _adjust_level(old_level, score)

    # 写入记录
    record = AssessmentRecord(
        user_id=current_user.id,
        session_id=session_id,
        question_id=question_id if qdata is None else None,  # DB 题目有 ID，动态题 NULL
        question_type=question_type,
        user_answer=answer if not is_speaking else (transcript or ""),
        is_correct=is_correct,
        score=score,
        audio_url=audio_url,
        transcript=transcript,
        question_order=session["question_order"],
        question_data=qdata if qdata else None,
    )
    db.add(record)
    db.commit()

    # 检查是否还有下一题
    next_index = session["question_order"]

    # 全对/全错追加题逻辑
    if next_index >= TOTAL_QUESTIONS:
        all_scores = []
        for dim_scores in session["dimension_totals"].values():
            all_scores.extend(dim_scores)

        if len(all_scores) >= TOTAL_QUESTIONS:
            correct_count = sum(1 for s in all_scores if s >= 60)

            if correct_count >= BONUS_THRESHOLD_CORRECT and not session.get("bonus_added"):
                # 全对 → 追加 1 题 C2 确认题
                session["bonus_added"] = True
                qdata, audio_b64 = await _generate_question(
                    db, "speaking", "C2", session, current_user.age_group,
                )
                qid = _next_dynamic_id()
                session["generated_questions"][qid] = qdata
                bonus_item = QuestionItem(
                    id=qid, type="speaking", difficulty="C2",
                    content=qdata["question_text"],
                    options=qdata.get("options", []),
                    audio_base64=audio_b64,
                )
                logger.info(f"全对追加 C2 确认题: session={session_id}")
                return AssessmentAnswerResponse(
                    complete=False,
                    next_question=bonus_item,
                    current_difficulty="C2",
                )

            elif correct_count <= BONUS_THRESHOLD_WRONG and not session.get("bonus_added"):
                # 全错 → 追加 1 题 A1 兜底题
                session["bonus_added"] = True
                qdata, audio_b64 = await _generate_question(
                    db, "listening", "A1", session, current_user.age_group,
                )
                qid = _next_dynamic_id()
                session["generated_questions"][qid] = qdata
                bonus_item = QuestionItem(
                    id=qid, type="listening", difficulty="A1",
                    content=qdata["question_text"],
                    options=qdata.get("options", []),
                    audio_base64=audio_b64,
                )
                logger.info(f"全错追加 A1 兜底题: session={session_id}")
                return AssessmentAnswerResponse(
                    complete=False,
                    next_question=bonus_item,
                    current_difficulty="A1",
                )

    if next_index >= TOTAL_QUESTIONS and (
        not session.get("bonus_added") or next_index > TOTAL_QUESTIONS
    ):
        return AssessmentAnswerResponse(
            complete=True,
            next_question=None,
            current_difficulty=_level_to_cefr(session["current_level"]),
        )

    # LLM 动态生成下一题
    next_dim = _pick_next_dimension(session)
    target_cefr = _level_to_cefr(session["current_level"])
    qdata, audio_b64 = await _generate_question(
        db, next_dim, target_cefr, session, current_user.age_group,
    )
    qid = _next_dynamic_id()
    session["generated_questions"][qid] = qdata

    next_question = QuestionItem(
        id=qid,
        type=next_dim,
        difficulty=target_cefr,
        content=qdata["question_text"],
        options=qdata.get("options", []),
        audio_base64=audio_b64,
    )

    logger.info(
        f"动态测评答题: user={current_user.username}, qid={question_id}, "
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
    generated_questions = {}
    current_level = 3.0
    consecutive_correct = 0
    consecutive_wrong = 0

    for rec in records:
        answered_ids.add(rec.question_id if rec.question_id else rec.question_order)
        if rec.question_data:
            # 动态题目，从 question_data 恢复
            qdata = rec.question_data if isinstance(rec.question_data, dict) else json.loads(str(rec.question_data))
            generated_questions[rec.question_id or (-rec.question_order)] = qdata
            dim = qdata.get("dimension", "grammar")
        else:
            question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == rec.question_id).first()
            dim = question.dimension if question else "grammar"

        if rec.score is not None:
            dimension_totals[dim].append(float(rec.score))
            current_level = _adjust_level(current_level, float(rec.score))
            if rec.is_correct == 1:
                consecutive_correct += 1
                consecutive_wrong = 0
            elif rec.is_correct == 0:
                consecutive_wrong += 1
                consecutive_correct = 0

    _sessions[session_id] = {
        "user_id": current_user.id,
        "current_level": current_level,
        "dimension_totals": dimension_totals,
        "question_order": len(records),
        "answered_ids": answered_ids,
        "generated_questions": generated_questions,
        "consecutive_correct": consecutive_correct,
        "consecutive_wrong": consecutive_wrong,
        "start_time": (_sessions.get(session_id) or {}).get("start_time") or time.time(),
        "bonus_added": len(records) > TOTAL_QUESTIONS,
    }

    # 还有下一题就动态生成
    next_index = len(records)
    if next_index >= TOTAL_QUESTIONS and not (len(records) > TOTAL_QUESTIONS):
        return {"complete": True, "answered_count": len(records)}

    next_dim = _pick_next_dimension(_sessions[session_id])
    target_cefr = _level_to_cefr(current_level)
    qdata, audio_b64 = await _generate_question(
        db, next_dim, target_cefr, _sessions[session_id], current_user.age_group,
    )
    qid = _next_dynamic_id()
    _sessions[session_id]["generated_questions"][qid] = qdata

    next_question = QuestionItem(
        id=qid, type=next_dim, difficulty=target_cefr,
        content=qdata["question_text"],
        options=qdata.get("options", []),
        audio_base64=audio_b64,
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

    # CEFR 定级（考虑年龄段偏移）
    level, label = _get_cefr(overall, current_user.age_group)

    # 短板维度
    weakness_dim = min(dimension_scores, key=dimension_scores.get)
    weakness = {
        "dimension": weakness_dim,
        "score": dimension_scores[weakness_dim],
        "label": DIMENSION_LABELS.get(weakness_dim, weakness_dim),
        "suggestion": SUGGESTIONS.get(weakness_dim, ""),
    }

    # 计算实际用时
    start_time = session.get("start_time")
    duration_seconds = int(time.time() - start_time) if start_time else 0

    # 更新用户画像
    current_user.level_test = level
    current_user.level_final = level
    current_user.assessment_completed = 1
    db.commit()

    # 摄入测评分数到动态画像（写入 UserSkillScore + 触发 recalculate + 生成 DimensionScoreLog）
    from app.services.profile_updater import profile_updater
    profile_updater.ingest_assessment_scores(
        current_user.id, dimension_scores, session_id, db,
    )
    db.commit()

    # 查询该会话所有答题记录，构建逐题详情
    records = (
        db.query(AssessmentRecord)
        .filter(
            AssessmentRecord.session_id == session_id,
            AssessmentRecord.user_id == current_user.id,
        )
        .order_by(AssessmentRecord.question_order)
        .all()
    )

    questions_detail = []
    for rec in records:
        # 获取题目数据
        qdata = None
        if rec.question_data:
            qdata = rec.question_data if isinstance(rec.question_data, dict) else json.loads(str(rec.question_data))
        elif rec.question_id:
            db_q = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == rec.question_id).first()
            if db_q:
                qdata = {
                    "question_text": db_q.question_text,
                    "correct_option": db_q.correct_option,
                    "dimension": db_q.dimension,
                    "difficulty": db_q.difficulty,
                    "options": db_q.options,
                }

        dim = qdata.get("dimension", "grammar") if qdata else "grammar"
        difficulty = qdata.get("difficulty", "B1") if qdata else "B1"
        question_text = qdata.get("question_text", "") if qdata else ""

        # 正确答案
        correct_answer = None
        if qdata:
            co = qdata.get("correct_option", 1)
            try:
                co_int = int(co)
                correct_answer = chr(64 + co_int)  # 1→A, 2→B
            except (ValueError, TypeError):
                correct_answer = str(co)

        questions_detail.append({
            "order": rec.question_order,
            "type": dim,
            "type_label": DIMENSION_LABELS.get(dim, dim),
            "difficulty": difficulty,
            "content": question_text[:80] + ("..." if len(question_text) > 80 else ""),
            "user_answer": rec.user_answer[:60] if rec.user_answer else None,
            "correct_answer": correct_answer if rec.question_type == "multiple_choice" else None,
            "is_correct": bool(rec.is_correct) if rec.is_correct is not None else None,
            "score": float(rec.score) if rec.score else 0.0,
            "transcript": rec.transcript[:100] if rec.transcript else None,
        })

    # 清理会话
    del _sessions[session_id]

    logger.info(
        f"用户 {current_user.username} 完成测评: overall={overall}, level={level}, "
        f"duration={duration_seconds}s, questions={len(questions_detail)}"
    )

    return AssessmentSubmitResponse(
        overall=overall,
        cefr_level=CEFRLevel(level=level, label=label),
        dimension_scores=dimension_scores,
        weakness=weakness,
        duration=duration_seconds,
        questions_detail=questions_detail,
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
    level, label = _get_cefr(overall, current_user.age_group)

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