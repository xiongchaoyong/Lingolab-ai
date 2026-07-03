"""角色扮演 API — 向后兼容 wrapper（mode=role）

所有逻辑已迁移至 voice_chat.py，旧端点通过硬编码 mode="role" 保持兼容。
"""
# 完全委托给 voice_chat 的共享会话和辅助函数
# 核心差异：mode="role", MAX_ROUNDS=6, ROLE_OPENERS/ROLE_NAMES

import os, base64, uuid, tempfile, subprocess, logging, asyncio, json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.roleplay import (
    RoleplayStartRequest, RoleplayStartResponse,
    RoleplaySpeakResponse, RoleplayEndResponse,
)
from app.models.conversation import ConversationSession, ConversationMessage
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.tts import synthesize_speech
from app.services.pronunciation import score_audio
from app.services.fluency import assess_algorithmic, aggregate_fluency
from app.services.audio_utils import convert_to_wav

from app.api.voice_chat import _sessions, _init_session, _tts_to_base64, ROLE_OPENERS, ROLE_NAMES

router = APIRouter()
logger = logging.getLogger(__name__)
MAX_ROUNDS = 6
MODE = "role"


@router.post("/start", response_model=RoleplayStartResponse)
async def roleplay_start(
    req: RoleplayStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = uuid.uuid4().hex[:12]
    topic = req.topic
    cefr_level = req.cefr_level

    db_session_id = None
    try:
        db_session = ConversationSession(
            user_id=current_user.id, session_uuid=session_id,
            scene="free", role_id=list(ROLE_NAMES.keys()).index(topic) + 1 if topic in ROLE_NAMES else 0,
            cefr_level=cefr_level, status="active",
        )
        db.add(db_session)
        db.commit()
        db_session_id = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话到 DB 失败: {e}")

    _init_session(session_id, topic, MODE, cefr_level, db_session_id)

    opener = ROLE_OPENERS.get(topic, ROLE_OPENERS["interviewee"])
    llm = get_llm_service()
    ai_text = await llm.chat(topic, opener, [], cefr_level, mode=MODE)

    _sessions[session_id]["history"].append({"role": "ai", "text": ai_text})

    logger.info(f"角色扮演开始: session={session_id}, role={topic}, level={cefr_level}")
    return RoleplayStartResponse(session_id=session_id, ai_text=ai_text, ai_audio_base64="")


@router.post("/speak", response_model=RoleplaySpeakResponse)
async def roleplay_speak(
    session_id: str = Form(...),
    role: str = Form(default="interviewee"),
    audio: UploadFile = File(...),
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    cefr_level = session["cefr_level"]

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path, converted_path, user_text = None, None, ""

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        converted_path = convert_to_wav(tmp_path)

        asr = get_asr_service()
        asr_result = asr.transcribe(converted_path)
        user_text = asr_result.get("text", "").strip()

        if not user_text:
            return RoleplaySpeakResponse(
                user_text="(未识别到语音)",
                ai_text="I didn't catch that. Could you say it again?",
                ai_audio_base64="",
            )

        session["history"].append({"role": "user", "text": user_text})
        session["round"] += 1

        try:
            words = asr_result.get("words", [])
            audio_duration = asr_result.get("segments", [{}])[-1].get("end", 5.0) if asr_result.get("segments") else 5.0
            fluency_algo = assess_algorithmic(user_text, words, audio_duration)
            session["fluency_scores"].append({
                "text": user_text, "wpm": fluency_algo["wpm"],
                "pause_frequency": fluency_algo["pause_frequency"],
                "repetition": fluency_algo["repetition"],
            })
        except Exception as e:
            logger.warning(f"流利度算法计算失败: {e}")

        llm = get_llm_service()
        grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

        ai_text = await llm.chat(role, user_text, session["history"][:-1], cefr_level, mode=MODE)
        session["history"].append({"role": "ai", "text": ai_text})

        grammar_correction = None
        try:
            grammar_result = await grammar_task
            if grammar_result.get("errors"):
                grammar_correction = grammar_result
        except Exception as e:
            logger.warning(f"语法纠错失败: {e}")

        return RoleplaySpeakResponse(
            user_text=user_text, ai_text=ai_text, ai_audio_base64="",
            grammar_correction=grammar_correction,
            conversation_complete=session["round"] >= MAX_ROUNDS,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"音频转码失败: {e.stderr.decode() if e.stderr else str(e)}")
        raise HTTPException(status_code=422, detail="音频格式无法识别")
    except Exception as e:
        logger.error(f"角色扮演处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if converted_path:
            session["user_audios"].append((converted_path, user_text))
        try:
            if tmp_path: os.unlink(tmp_path)
        except Exception: pass


# stream/start, stream/speak, tts, end 等端点委托给 voice_chat 处理
# 但由于它们包含流式生成器，最简单的兼容方式是保留原有逻辑
# 此处仅包含核心端点；完整功能请使用 /api/voice-chat

@router.post("/stream/start")
async def roleplay_stream_start(
    req: RoleplayStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.schemas.voice_chat import VoiceChatStartRequest
    from app.api.voice_chat import voice_chat_stream_start
    voice_req = VoiceChatStartRequest(topic=req.topic, mode="role", cefr_level=req.cefr_level)
    return await voice_chat_stream_start(voice_req, current_user, db)


@router.post("/stream/speak")
async def roleplay_stream_speak(
    session_id: str = Form(...),
    role: str = Form(default="interviewee"),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    from app.api.voice_chat import voice_chat_stream_speak
    return await voice_chat_stream_speak(session_id, audio, db)


@router.post("/tts")
async def roleplay_tts(text: str = Form(...), voice: str = Form(default="en-US-JennyNeural")):
    from app.api.voice_chat import voice_chat_tts
    return await voice_chat_tts(text, voice)


@router.get("/tts/stream")
async def roleplay_tts_stream(text: str = Query(...), voice: str = Query(default="en-US-JennyNeural")):
    from app.api.voice_chat import voice_chat_tts_stream
    return await voice_chat_tts_stream(text, voice)


@router.get("/tts/cached/{session_id}/{round_key}")
async def roleplay_tts_cached(session_id: str, round_key: str):
    from app.api.voice_chat import voice_chat_tts_cached
    return await voice_chat_tts_cached(session_id, round_key)


@router.post("/end", response_model=RoleplayEndResponse)
async def roleplay_end(
    session_id: str = Form(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    history = session["history"]
    cefr_level = session["cefr_level"]
    user_audios = session.get("user_audios", [])
    age_group = current_user.age_group

    dimensions, pronunciation, dimension_details, utterances = [], [], [], []
    overall = 0; suggestions = ""; scoring_methodology = ""; fluency_report = None

    user_messages = [h for h in history if h["role"] == "user"]

    try:
        if user_audios:
            all_dim_scores = {k: [] for k in ("音素准确度", "重音位置", "语调曲线", "连读表现", "节奏感")}
            for wav_path, asr_text in user_audios:
                try:
                    result = await score_audio(wav_path, asr_text, mode="sentence")
                    utterances.append({
                        "text": asr_text, "overall": result.get("overall"),
                        "dimensions": result.get("dimensions"), "errors": result.get("errors"),
                        "char_scores": result.get("char_scores"),
                        "analysis_detail": result.get("analysis_detail"),
                    })
                    for dim in result.get("dimensions", []):
                        key = dim["label"]
                        if key in all_dim_scores: all_dim_scores[key].append(dim["score"])
                except Exception as e:
                    logger.warning(f"单段音频发音评测失败: {e}")
                    continue
            for label, scores in all_dim_scores.items():
                if scores: pronunciation.append({"label": label, "score": round(sum(scores) / len(scores))})

        if len(user_messages) >= 1:
            llm = get_llm_service()
            rp_result = await llm.score_roleplay(history, cefr_level, age_group)
            dimensions = [
                {"label": "角色贴合度", "score": rp_result.get("role_fit", 75)},
                {"label": "场景礼仪", "score": rp_result.get("etiquette", 75)},
                {"label": "专业术语", "score": rp_result.get("terminology", 75)},
                {"label": "应对能力", "score": rp_result.get("response", 75)},
            ]
            dimension_details = [
                {"label": "角色贴合度", "score": rp_result.get("role_fit", 75), "feedback": rp_result.get("role_fit_feedback", ""), "strengths": rp_result.get("role_fit_strengths", ""), "weaknesses": rp_result.get("role_fit_weaknesses", "")},
                {"label": "场景礼仪", "score": rp_result.get("etiquette", 75), "feedback": rp_result.get("etiquette_feedback", ""), "strengths": rp_result.get("etiquette_strengths", ""), "weaknesses": rp_result.get("etiquette_weaknesses", "")},
                {"label": "专业术语", "score": rp_result.get("terminology", 75), "feedback": rp_result.get("terminology_feedback", ""), "strengths": rp_result.get("terminology_strengths", ""), "weaknesses": rp_result.get("terminology_weaknesses", "")},
                {"label": "应对能力", "score": rp_result.get("response", 75), "feedback": rp_result.get("response_feedback", ""), "strengths": rp_result.get("response_strengths", ""), "weaknesses": rp_result.get("response_weaknesses", "")},
            ]
            suggestions = rp_result.get("suggestions", "")
        else:
            dimensions = [{"label": "角色贴合度", "score": 0}, {"label": "场景礼仪", "score": 0}, {"label": "专业术语", "score": 0}, {"label": "应对能力", "score": 0}]
            suggestions = "还没有开口说话，无法评估。再来一次试试吧！"

        from app.services.age_adaptive import get_roleplay_role_weights
        role_weights = get_roleplay_role_weights(age_group)
        role_avg = sum(d["score"] * role_weights.get(d["label"], 0.25) for d in dimensions) if dimensions else 0
        pron_avg = sum(d["score"] for d in pronunciation) / len(pronunciation) if pronunciation else 0

        if dimensions and pronunciation: overall = round(role_avg * 0.6 + pron_avg * 0.4)
        elif dimensions: overall = round(role_avg)
        elif pronunciation: overall = round(pron_avg)

        w = role_weights
        scoring_methodology = (
            f"综合分 = 角色表现加权分 × 60% + 发音均分 × 40%（{age_group}自适应权重）\n"
            f"角色表现（LLM 评估）：角色贴合度({w.get('角色贴合度',0.40):.0%})、"
            f"场景礼仪({w.get('场景礼仪',0.25):.0%})、专业术语({w.get('专业术语',0.20):.0%})、"
            f"应对能力({w.get('应对能力',0.15):.0%})\n"
            "发音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感"
        )

        fluency_scores = session.get("fluency_scores", [])
        if fluency_scores and len(user_messages) >= 1:
            try:
                llm_utterances = []
                for i, fs in enumerate(fluency_scores):
                    context = ""
                    for j in range(len(history)):
                        if history[j].get("role") == "user" and history[j]["text"] == fs["text"]:
                            if j > 0 and history[j - 1]["role"] == "ai":
                                context = history[j - 1]["text"]
                            break
                    llm_utterances.append({"round": i + 1, "text": fs["text"], "context": context})
                llm = get_llm_service()
                fluency_llm_result = await llm.score_fluency(llm_utterances, cefr_level, session.get("topic", ""))
                llm_rounds = fluency_llm_result.get("rounds", [])
                for i, fs in enumerate(fluency_scores):
                    if i < len(llm_rounds):
                        fs["llm"] = {"grammar": llm_rounds[i].get("grammar", {"score": 15, "errors": [], "max": 20}), "relevance": llm_rounds[i].get("relevance", {"score": 10, "max": 15, "note": ""})}
                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = fluency_llm_result.get("overall_suggestions", "")
            except Exception as e:
                logger.warning(f"角色扮演流利度 LLM 评估失败: {e}")
                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = "流利度评估仅供参考，多说多练！"
    except Exception as e:
        logger.error(f"角色扮演评分失败: {e}")
        dimensions = [{"label": "角色贴合度", "score": 0}, {"label": "场景礼仪", "score": 0}, {"label": "专业术语", "score": 0}, {"label": "应对能力", "score": 0}]
        overall = 0; suggestions = "评分服务暂时异常，请稍后重试"
    finally:
        for wav_path, _ in user_audios:
            try:
                if os.path.exists(wav_path): os.unlink(wav_path)
            except Exception: pass
        try:
            db_session_id = session.get("db_session_id") if session else None
            if db_session_id:
                db.query(ConversationSession).filter(ConversationSession.id == db_session_id).update({
                    "round_count": session.get("round", 0), "status": "completed",
                    "score_pronunciation": round(sum(d["score"] for d in pronunciation) / len(pronunciation), 2) if pronunciation else None,
                    "score_grammar": next((d["score"] for d in dimensions if d["label"] == "场景礼仪"), None),
                    "score_vocabulary": next((d["score"] for d in dimensions if d["label"] == "专业术语"), None),
                    "score_engagement": next((d["score"] for d in dimensions if d["label"] == "应对能力"), None),
                    "score_overall": overall, "improvement_suggestions": suggestions, "ended_at": func.now(),
                })
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"保存角色扮演评分到 DB 失败: {e}")
        if session_id in _sessions:
            del _sessions[session_id]

    return RoleplayEndResponse(
        overall=overall, dimensions=dimensions, suggestions=suggestions,
        utterances=utterances, transcript=history, pronunciation=pronunciation,
        dimension_details=dimension_details, scoring_methodology=scoring_methodology,
        fluency=fluency_report,
    )
