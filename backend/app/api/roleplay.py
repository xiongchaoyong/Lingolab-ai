"""角色扮演 API 路由 — 复用 ASR → LLM(角色Prompt) → TTS 管线"""

import os
import io
import base64
import uuid
import tempfile
import subprocess
import logging
import asyncio

import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.conversation import ConversationSession, ConversationMessage

from app.schemas.roleplay import (
    RoleplayStartRequest,
    RoleplayStartResponse,
    RoleplaySpeakResponse,
    RoleplayEndResponse,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.tts import synthesize_speech
from app.services.pronunciation import score_audio
from app.services.fluency import assess_algorithmic, aggregate_fluency
from app.services.audio_utils import convert_to_wav

router = APIRouter()
logger = logging.getLogger(__name__)

# 内存会话存储
_sessions: dict[str, dict] = {}

MAX_CONVERSATION_ROUNDS = 6

# 角色开场白 Prompt
ROLE_OPENERS = {
    "interviewee": "Start the job interview. Greet the candidate and ask them to introduce themselves.",
    "waiter": "Enter the restaurant as a customer. Greet the waiter and ask for a table.",
    "guide": "Meet your tour guide at the attraction. Greet them and ask about the site's history.",
    "doctor": "Enter the clinic as a patient. Greet the doctor and describe your symptoms.",
    "teacher": "Enter the classroom as a student. Greet the teacher and ask a question about today's lesson.",
    "customer_service": "Call the customer service hotline. Greet the representative and explain your product issue.",
    "receptionist": "Approach the hotel front desk as a guest. Greet the receptionist and ask to check in.",
    "colleague": "Meet the new team member at the office. Greet them and offer to show them around.",
}

# 角色中文名
ROLE_NAMES = {
    "interviewee": "面试者",
    "waiter": "服务员",
    "guide": "导游",
    "doctor": "医生",
    "teacher": "老师",
    "customer_service": "客服",
    "receptionist": "前台接待",
    "colleague": "同事",
}


async def _tts_to_base64(text: str, voice: str = "en-US-JennyNeural") -> str:
    """生成 TTS 音频并返回 base64 编码"""
    audio_bytes = await synthesize_speech(text, voice)
    return base64.b64encode(audio_bytes).decode("utf-8")


@router.post("/start", response_model=RoleplayStartResponse)
async def roleplay_start(
    req: RoleplayStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始角色扮演

    返回 session_id + AI 角色开场白，语音通过 /tts 接口异步获取
    """
    session_id = uuid.uuid4().hex[:12]
    role = req.role
    cefr_level = req.cefr_level

    # 初始化会话
    _sessions[session_id] = {
        "role": role,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],
        "fluency_scores": [],  # 每轮流利度算法评分
        "tts_cache": {},  # TTS 预取缓存
    }

    # 持久化到 DB（复用 conversation_sessions 表，scene 设为 roleplay 角色名）
    try:
        db_session = ConversationSession(
            user_id=current_user.id,
            session_uuid=session_id,
            scene="free",  # roleplay 复用 free 场景
            role_id=list(ROLE_NAMES.keys()).index(role) + 1 if role in ROLE_NAMES else 0,
            cefr_level=cefr_level,
            status="active",
        )
        db.add(db_session)
        db.commit()
        _sessions[session_id]["db_session_id"] = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存角色扮演会话到 DB 失败: {e}")

    # 生成 AI 角色开场白
    opener = ROLE_OPENERS.get(role, ROLE_OPENERS["interviewee"])

    llm = get_llm_service()
    ai_text = await llm.chat_roleplay(
        role=role,
        user_text=opener,
        history=[],
        cefr_level=cefr_level,
    )

    # 记录 AI 消息
    _sessions[session_id]["history"].append({"role": "ai", "text": ai_text})

    logger.info(f"角色扮演开始: session={session_id}, role={role}, level={cefr_level}")
    return RoleplayStartResponse(
        session_id=session_id,
        ai_text=ai_text,
        ai_audio_base64="",
    )


@router.post("/speak", response_model=RoleplaySpeakResponse)
async def roleplay_speak(
    session_id: str = Form(..., description="会话 ID"),
    role: str = Form(default="interviewee", description="角色标识"),
    audio: UploadFile = File(..., description="用户语音"),
):
    """
    用户说话 — 角色扮演

    流程：音频转写(ASR) → LLM(角色Prompt) → TTS
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    cefr_level = session["cefr_level"]

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 转码
        converted_path = convert_to_wav(tmp_path)

        # ASR 转写
        asr = get_asr_service()
        asr_result = asr.transcribe(converted_path)
        user_text = asr_result.get("text", "").strip()

        if not user_text:
            return RoleplaySpeakResponse(
                user_text="(未识别到语音)",
                ai_text="I didn't catch that. Could you say it again?",
                ai_audio_base64="",
            )

        logger.info(f"角色扮演 ASR: '{user_text[:80]}...'")

        # 记录用户消息
        session["history"].append({"role": "user", "text": user_text})
        session["round"] += 1

        # 算法流利度计算（维度1-3，静默存储）
        try:
            words = asr_result.get("words", [])
            audio_duration = asr_result.get("segments", [{}])[-1].get("end", 5.0) if asr_result.get("segments") else 5.0
            fluency_algo = assess_algorithmic(user_text, words, audio_duration)
            session["fluency_scores"].append({
                "text": user_text,
                "wpm": fluency_algo["wpm"],
                "pause_frequency": fluency_algo["pause_frequency"],
                "repetition": fluency_algo["repetition"],
            })
        except Exception as e:
            logger.warning(f"流利度算法计算失败: {e}")

        # LLM 角色回复 + 语法纠错（并行）
        llm = get_llm_service()
        grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

        ai_text = await llm.chat_roleplay(
            role=role,
            user_text=user_text,
            history=session["history"][:-1],
            cefr_level=cefr_level,
        )

        # 记录 AI 消息
        session["history"].append({"role": "ai", "text": ai_text})

        # 等待语法纠错结果
        grammar_correction = None
        try:
            grammar_result = await grammar_task
            if grammar_result.get("errors"):
                grammar_correction = grammar_result
        except Exception as e:
            logger.warning(f"语法纠错失败: {e}")

        conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS

        return RoleplaySpeakResponse(
            user_text=user_text,
            ai_text=ai_text,
            ai_audio_base64="",
            grammar_correction=grammar_correction,
            conversation_complete=conversation_complete,
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"音频转码失败: {e.stderr.decode() if e.stderr else str(e)}")
        raise HTTPException(status_code=422, detail="音频格式无法识别")
    except Exception as e:
        logger.error(f"角色扮演处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if converted_path:
            session["user_audios"].append((converted_path, user_text if 'user_text' in dir() else ""))
        try:
            if tmp_path:
                os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/stream/start")
async def roleplay_stream_start(
    req: RoleplayStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    流式开始角色扮演 — SSE 逐 token 返回 AI 开场白
    """
    session_id = uuid.uuid4().hex[:12]
    role = req.role
    cefr_level = req.cefr_level

    _sessions[session_id] = {
        "role": role,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],
        "fluency_scores": [],  # 每轮流利度算法评分
        "tts_cache": {},  # TTS 预取缓存
    }

    # 持久化到 DB
    try:
        db_session = ConversationSession(
            user_id=current_user.id,
            session_uuid=session_id,
            scene="free",
            role_id=list(ROLE_NAMES.keys()).index(role) + 1 if role in ROLE_NAMES else 0,
            cefr_level=cefr_level,
            status="active",
        )
        db.add(db_session)
        db.commit()
        _sessions[session_id]["db_session_id"] = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存角色扮演会话到 DB 失败: {e}")

    opener = ROLE_OPENERS.get(role, ROLE_OPENERS["interviewee"])
    llm = get_llm_service()

    async def generate():
        full_text = ""
        try:
            async for token in llm.chat_roleplay_stream(role, opener, [], cefr_level):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            _sessions[session_id]["history"].append({"role": "ai", "text": full_text})

            # TTS 预取：后台启动 Edge TTS 调用，缓存音频块
            round_key = "0"
            chunks = []
            cache_entry = {"chunks": chunks, "done": False}
            _sessions[session_id]["tts_cache"][round_key] = cache_entry

            async def prefetch_tts():
                try:
                    import edge_tts
                    communicate = edge_tts.Communicate(full_text, "en-US-JennyNeural")
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            chunks.append(chunk["data"])
                except Exception as e:
                    logger.error(f"TTS 预取失败: {e}")
                finally:
                    cache_entry["done"] = True

            asyncio.create_task(prefetch_tts())

            tts_url = f"/api/roleplay/tts/cached/{session_id}/{round_key}"
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'full_text': full_text, 'tts_url': tts_url})}\n\n"
        except Exception as e:
            logger.error(f"角色扮演流式 start 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/stream/speak")
async def roleplay_stream_speak(
    session_id: str = Form(..., description="会话 ID"),
    role: str = Form(default="interviewee", description="角色标识"),
    audio: UploadFile = File(..., description="用户语音"),
    db: Session = Depends(get_db),
):
    """
    流式角色扮演对话 — ASR 后 SSE 逐 token 返回 AI 回复
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    cefr_level = session["cefr_level"]

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        converted_path = convert_to_wav(tmp_path)
    except Exception:
        for path in (tmp_path, converted_path):
            try:
                if path:
                    os.unlink(path)
            except Exception:
                pass
        raise HTTPException(status_code=422, detail="音频处理失败")

    async def generate():
        nonlocal tmp_path, converted_path
        user_text = ""
        try:
            asr = get_asr_service()
            asr_result = asr.transcribe(converted_path)
            user_text = asr_result.get("text", "").strip()

            if not user_text:
                yield f"data: {json.dumps({'type': 'asr', 'text': '(未识别到语音)'})}\n\n"
                yield f'data: {{"type": "done", "full_text": "I didn\'t catch that. Could you say it again?"}}\n\n'
                return

            yield f"data: {json.dumps({'type': 'asr', 'text': user_text})}\n\n"

            session["history"].append({"role": "user", "text": user_text})
            session["round"] += 1

            # 持久化用户消息
            db_msg_id = None
            try:
                db_sid = session.get("db_session_id")
                if db_sid:
                    db_msg = ConversationMessage(
                        session_id=db_sid, round_number=session["round"],
                        role="user", content_text=user_text,
                    )
                    db.add(db_msg)
                    db.commit()
                    db.refresh(db_msg)
                    db_msg_id = db_msg.id
            except Exception as e:
                db.rollback()
                logger.warning(f"保存角色扮演用户消息失败: {e}")

            # 算法流利度计算（维度1-3，静默存储）
            try:
                words = asr_result.get("words", [])
                segments = asr_result.get("segments", [])
                audio_duration = segments[-1].get("end", 5.0) if segments else 5.0
                fluency_algo = assess_algorithmic(user_text, words, audio_duration)
                session["fluency_scores"].append({
                    "text": user_text,
                    "wpm": fluency_algo["wpm"],
                    "pause_frequency": fluency_algo["pause_frequency"],
                    "repetition": fluency_algo["repetition"],
                })
            except Exception as e:
                logger.warning(f"流利度算法计算失败: {e}")

            # 语法纠错 + 翻译（后台并行，与 LLM 回复同时进行，不增加延迟）
            llm = get_llm_service()
            grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

            full_text = ""
            async for token in llm.chat_roleplay_stream(
                role, user_text, session["history"][:-1], cefr_level
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            session["history"].append({"role": "ai", "text": full_text})
            conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS

            # AI 回复翻译（后台并行）
            translation_task = asyncio.create_task(llm.translate_to_chinese(full_text))

            # 持久化 AI 回复
            try:
                db_sid = session.get("db_session_id")
                if db_sid:
                    db.add(ConversationMessage(
                        session_id=db_sid, round_number=session["round"],
                        role="assistant", content_text=full_text,
                    ))
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"保存角色扮演 AI 消息失败: {e}")

            # TTS 预取：后台启动 Edge TTS 调用，缓存音频块
            round_key = str(session["round"])
            chunks = []
            cache_entry = {"chunks": chunks, "done": False}
            session["tts_cache"][round_key] = cache_entry

            async def prefetch_tts():
                try:
                    import edge_tts
                    communicate = edge_tts.Communicate(full_text, "en-US-JennyNeural")
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            chunks.append(chunk["data"])
                except Exception as e:
                    logger.error(f"TTS 预取失败: {e}")
                finally:
                    cache_entry["done"] = True

            asyncio.create_task(prefetch_tts())

            tts_url = f"/api/roleplay/tts/cached/{session_id}/{round_key}"
            # 先发送 done 事件，前端可立即播放 TTS，语法纠错不阻塞对话流
            yield f"data: {json.dumps({'type': 'done', 'full_text': full_text, 'conversation_complete': conversation_complete, 'tts_url': tts_url})}\n\n"

            # 等待语法纠错结果（后台已并行执行，不阻塞 TTS 播放）
            try:
                grammar_result = await grammar_task
                if grammar_result.get("errors"):
                    yield f"data: {json.dumps({'type': 'grammar', 'data': grammar_result})}\n\n"
                    # 存入会话历史，评分报告中的对话记录可展示纠错
                    session["history"].append({"role": "grammar", "text": grammar_result})

                # 持久化语法纠错到 conversation_messages
                if db_msg_id and grammar_result:
                    try:
                        db.query(ConversationMessage).filter(
                            ConversationMessage.id == db_msg_id
                        ).update({"grammar_check": grammar_result})
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.warning(f"保存语法纠错失败: {e}")
            except Exception as e:
                logger.warning(f"语法纠错失败: {e}")

            # 等待 AI 回复翻译结果
            try:
                translation = await translation_task
                if translation:
                    yield f"data: {json.dumps({'type': 'translation', 'data': translation})}\n\n"
            except Exception as e:
                logger.warning(f"翻译失败: {e}")

        except Exception as e:
            logger.error(f"角色扮演流式 speak 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            if converted_path and user_text:
                session["user_audios"].append((converted_path, user_text))
            try:
                if tmp_path:
                    os.unlink(tmp_path)
            except Exception:
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.post("/tts")
async def roleplay_tts(
    text: str = Form(..., description="要合成的文本"),
    voice: str = Form(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
    """文本转语音（独立接口）"""
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本不能为空")

    try:
        audio_base64 = await _tts_to_base64(text.strip(), voice)
        return {"audio_base64": audio_base64}
    except Exception as e:
        logger.error(f"角色扮演 TTS 失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.get("/tts/stream")
async def roleplay_tts_stream(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
    """
    流式文本转语音 — 直接返回 MP3 音频流

    浏览器可直接作为 <audio> 的 src 使用，边下载边播放。
    """
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本不能为空")

    text = text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=422, detail="文本过长")

    async def generate():
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"角色扮演流式 TTS 失败: {e}")

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/tts/cached/{session_id}/{round_key}")
async def roleplay_tts_cached(session_id: str, round_key: str):
    """
    获取预取的 TTS 音频缓存 — 后台 Edge TTS 调用完成后流式返回
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    cache = session.get("tts_cache", {}).get(round_key)
    if not cache:
        raise HTTPException(status_code=404, detail="TTS 缓存不存在")

    async def generate():
        idx = 0
        while True:
            while idx < len(cache["chunks"]):
                yield cache["chunks"][idx]
                idx += 1
            if cache["done"]:
                break
            await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/end", response_model=RoleplayEndResponse)
async def roleplay_end(
    session_id: str = Form(..., description="会话 ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    结束角色扮演并评分

    评分体系：
    1. 角色维度：LLM 四维评分（角色贴合度/场景礼仪/专业术语/应对能力）
    2. 语音维度：wav2vec2 发音评测（复用 conversation 的评分逻辑）
    3. 综合分 = 角色均分 × 0.6 + 语音均分 × 0.4
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    history = session["history"]
    cefr_level = session["cefr_level"]
    user_audios = session.get("user_audios", [])
    role = session.get("role", "interviewee")

    dimensions = []
    pronunciation = []
    utterances = []
    overall = 0
    suggestions = ""
    dimension_details = []
    scoring_methodology = ""
    fluency_report = None

    user_messages = [h for h in history if h["role"] == "user"]

    try:
        # 1. 语音评测
        if user_audios:
            logger.info(f"角色扮演发音评测，共 {len(user_audios)} 段音频")
            all_dim_scores = {k: [] for k in ("音素准确度", "重音位置", "语调曲线", "连读表现", "节奏感")}

            for wav_path, asr_text in user_audios:
                try:
                    result = await score_audio(wav_path, asr_text, mode="sentence")
                    utterances.append({
                        "text": asr_text,
                        "overall": result.get("overall"),
                        "dimensions": result.get("dimensions"),
                        "errors": result.get("errors"),
                        "char_scores": result.get("char_scores"),
                        "analysis_detail": result.get("analysis_detail"),
                    })
                    for dim in result.get("dimensions", []):
                        key = dim["label"]
                        if key in all_dim_scores:
                            all_dim_scores[key].append(dim["score"])
                except Exception as e:
                    logger.warning(f"单段音频发音评测失败: {e}")
                    continue

            for label, scores in all_dim_scores.items():
                if scores:
                    pronunciation.append({
                        "label": label,
                        "score": round(sum(scores) / len(scores)),
                    })

        # 2. 角色四维评分
        if len(user_messages) >= 1:
            llm = get_llm_service()
            rp_result = await llm.score_roleplay(history, cefr_level)

            dimensions = [
                {"label": "角色贴合度", "score": rp_result.get("role_fit", 75)},
                {"label": "场景礼仪", "score": rp_result.get("etiquette", 75)},
                {"label": "专业术语", "score": rp_result.get("terminology", 75)},
                {"label": "应对能力", "score": rp_result.get("response", 75)},
            ]
            dimension_details = [
                {
                    "label": "角色贴合度",
                    "score": rp_result.get("role_fit", 75),
                    "feedback": rp_result.get("role_fit_feedback", ""),
                    "strengths": rp_result.get("role_fit_strengths", ""),
                    "weaknesses": rp_result.get("role_fit_weaknesses", ""),
                },
                {
                    "label": "场景礼仪",
                    "score": rp_result.get("etiquette", 75),
                    "feedback": rp_result.get("etiquette_feedback", ""),
                    "strengths": rp_result.get("etiquette_strengths", ""),
                    "weaknesses": rp_result.get("etiquette_weaknesses", ""),
                },
                {
                    "label": "专业术语",
                    "score": rp_result.get("terminology", 75),
                    "feedback": rp_result.get("terminology_feedback", ""),
                    "strengths": rp_result.get("terminology_strengths", ""),
                    "weaknesses": rp_result.get("terminology_weaknesses", ""),
                },
                {
                    "label": "应对能力",
                    "score": rp_result.get("response", 75),
                    "feedback": rp_result.get("response_feedback", ""),
                    "strengths": rp_result.get("response_strengths", ""),
                    "weaknesses": rp_result.get("response_weaknesses", ""),
                },
            ]
            suggestions = rp_result.get("suggestions", "")
        else:
            dimensions = [
                {"label": "角色贴合度", "score": 0},
                {"label": "场景礼仪", "score": 0},
                {"label": "专业术语", "score": 0},
                {"label": "应对能力", "score": 0},
            ]
            suggestions = "还没有开口说话，无法评估。再来一次试试吧！"

        # 3. 综合分（角色表现加权：贴合度40% + 礼仪25% + 术语20% + 应对15%）
        role_weights = {"角色贴合度": 0.40, "场景礼仪": 0.25, "专业术语": 0.20, "应对能力": 0.15}
        role_avg = sum(
            d["score"] * role_weights.get(d["label"], 0.25) for d in dimensions
        ) if dimensions else 0
        pron_avg = sum(d["score"] for d in pronunciation) / len(pronunciation) if pronunciation else 0

        if dimensions and pronunciation:
            overall = round(role_avg * 0.6 + pron_avg * 0.4)
        elif dimensions:
            overall = round(role_avg)
        elif pronunciation:
            overall = round(pron_avg)

        scoring_methodology = (
            "综合分 = 角色表现加权分 × 60% + 发音均分 × 40%\n"
            "角色表现（LLM 评估）：角色贴合度(40%)、场景礼仪(25%)、专业术语(20%)、应对能力(15%)\n"
            "发音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感"
        )

        # 4. 流利度评估（SRS 3.3.3）
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
                    llm_utterances.append({
                        "round": i + 1,
                        "text": fs["text"],
                        "context": context,
                    })

                llm = get_llm_service()
                fluency_llm_result = await llm.score_fluency(
                    llm_utterances, cefr_level, role
                )

                llm_rounds = fluency_llm_result.get("rounds", [])
                for i, fs in enumerate(fluency_scores):
                    if i < len(llm_rounds):
                        fs["llm"] = {
                            "grammar": llm_rounds[i].get("grammar", {"score": 15, "errors": [], "max": 20}),
                            "relevance": llm_rounds[i].get("relevance", {"score": 10, "max": 15, "note": ""}),
                        }

                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = fluency_llm_result.get("overall_suggestions", "")
                logger.info(f"角色扮演流利度评估完成: overall={fluency_report['overall']}/100, grade={fluency_report['grade']}")
            except Exception as e:
                logger.warning(f"角色扮演流利度 LLM 评估失败，仅返回算法评分: {e}")
                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = "流利度评估仅供参考，多说多练！"

    except Exception as e:
        logger.error(f"角色扮演评分失败: {e}")
        dimensions = [
            {"label": "角色贴合度", "score": 0},
            {"label": "场景礼仪", "score": 0},
            {"label": "专业术语", "score": 0},
            {"label": "应对能力", "score": 0},
        ]
        overall = 0
        suggestions = "评分服务暂时异常，请稍后重试"

    finally:
        for wav_path, _ in user_audios:
            try:
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
            except Exception:
                pass

        # 更新 DB 会话评分
        try:
            db_session_id = session.get("db_session_id") if session else None
            if db_session_id:
                role_score = next((d["score"] for d in dimensions if d["label"] == "角色贴合度"), None)
                pron_score = round(sum(d["score"] for d in pronunciation) / len(pronunciation), 2) if pronunciation else None
                db.query(ConversationSession).filter(
                    ConversationSession.id == db_session_id
                ).update({
                    "round_count": session.get("round", 0),
                    "status": "completed",
                    "score_pronunciation": pron_score,
                    "score_grammar": next((d["score"] for d in dimensions if d["label"] == "场景礼仪"), None),
                    "score_vocabulary": next((d["score"] for d in dimensions if d["label"] == "专业术语"), None),
                    "score_engagement": next((d["score"] for d in dimensions if d["label"] == "应对能力"), None),
                    "score_overall": overall,
                    "improvement_suggestions": suggestions,
                    "ended_at": func.now(),
                })
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"保存角色扮演评分到 DB 失败: {e}")

        if session_id in _sessions:
            del _sessions[session_id]

    return RoleplayEndResponse(
        overall=overall,
        dimensions=dimensions,
        suggestions=suggestions,
        utterances=utterances,
        transcript=history,
        pronunciation=pronunciation,
        dimension_details=dimension_details,
        scoring_methodology=scoring_methodology,
        fluency=fluency_report,
    )