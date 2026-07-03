"""语音对话 API — 统一自由对话 + 角色扮演（ASR → LLM → TTS 管线）"""

import os
import io
import base64
import uuid
import tempfile
import subprocess
import logging
import asyncio
import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.models.conversation import ConversationSession, ConversationMessage
from app.schemas.voice_chat import (
    VoiceChatStartRequest,
    VoiceChatStartResponse,
    VoiceChatSpeakResponse,
    VoiceChatEndResponse,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.tts import synthesize_speech
from app.services.pronunciation import score_audio
from app.services.fluency import assess_algorithmic, aggregate_fluency
from app.services.audio_utils import convert_to_wav

router = APIRouter()
logger = logging.getLogger(__name__)

# 内存会话存储（生产环境应迁移至 Redis）
_sessions: dict[str, dict] = {}

MAX_ROUNDS = {"scene": 10, "role": 6}

# ========== 开场白 Prompt ==========

SCENE_OPENERS = {
    "self_intro": "Greet the user and ask them to introduce themselves.",
    "directions": "You are lost. Ask the user for directions to a nearby place.",
    "shopping": "Welcome the customer and ask what they are looking for.",
    "restaurant": "Greet the customer and ask if they have a reservation.",
    "hotel": "Greet the guest arriving at the hotel and ask if they have a reservation.",
    "airport": "Greet the passenger at the check-in counter and ask for their destination.",
    "hospital": "Greet the patient and ask what symptoms they are experiencing.",
    "school": "Greet the new classmate and ask about their major and interests.",
}

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

ROLE_NAMES = {
    "interviewee": "面试者", "waiter": "服务员", "guide": "导游",
    "doctor": "医生", "teacher": "老师", "customer_service": "客服",
    "receptionist": "前台接待", "colleague": "同事",
}


# ========== 辅助函数 ==========

async def _tts_to_base64(text: str, voice: str = "en-US-JennyNeural") -> str:
    audio_bytes = await synthesize_speech(text, voice)
    return base64.b64encode(audio_bytes).decode("utf-8")


def _get_openers(mode: str) -> dict:
    return SCENE_OPENERS if mode == "scene" else ROLE_OPENERS


def _get_default_topic(mode: str) -> str:
    return "self_intro" if mode == "scene" else "interviewee"


# ========== 内部逻辑函数（供旧路由 wrapper 复用） ==========

def _init_session(session_id: str, topic: str, mode: str, cefr_level: str, db_session_id: int = None) -> dict:
    """初始化内存会话"""
    session = {
        "topic": topic,
        "mode": mode,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],
        "fluency_scores": [],
        "tts_cache": {},
        "db_session_id": db_session_id,
    }
    _sessions[session_id] = session
    return session


# ========== API 端点 ==========

@router.post("/start", response_model=VoiceChatStartResponse)
async def voice_chat_start(
    req: VoiceChatStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = uuid.uuid4().hex[:12]
    topic = req.topic
    mode = req.mode
    cefr_level = req.cefr_level

    # 持久化到 DB
    db_session_id = None
    try:
        db_session = ConversationSession(
            user_id=current_user.id,
            session_uuid=session_id,
            scene=topic,
            cefr_level=cefr_level,
            status="active",
        )
        db.add(db_session)
        db.commit()
        db_session_id = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话到 DB 失败: {e}")

    _init_session(session_id, topic, mode, cefr_level, db_session_id)

    openers = _get_openers(mode)
    opener = openers.get(topic, openers[_get_default_topic(mode)])

    llm = get_llm_service()
    ai_text = await llm.chat(topic, opener, [], cefr_level, mode=mode)

    _sessions[session_id]["history"].append({"role": "ai", "text": ai_text})

    logger.info(f"语音对话开始: session={session_id}, topic={topic}, mode={mode}, level={cefr_level}")
    return VoiceChatStartResponse(
        session_id=session_id,
        ai_text=ai_text,
        ai_audio_base64="",
        mode=mode,
        max_rounds=MAX_ROUNDS[mode],
    )


@router.post("/speak", response_model=VoiceChatSpeakResponse)
async def voice_chat_speak(
    session_id: str = Form(..., description="会话 ID"),
    audio: UploadFile = File(..., description="用户语音"),
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    mode = session["mode"]
    cefr_level = session["cefr_level"]
    topic = session["topic"]

    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = os.path.splitext(audio.filename)[1] or ".webm"

    tmp_path = None
    converted_path = None
    user_text = ""

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        converted_path = convert_to_wav(tmp_path)

        asr = get_asr_service()
        asr_result = asr.transcribe(converted_path)
        user_text = asr_result.get("text", "").strip()

        if not user_text:
            return VoiceChatSpeakResponse(
                user_text="(未识别到语音)",
                ai_text="I didn't catch that. Could you say it again?",
                ai_audio_base64="",
            )

        logger.info(f"ASR 转写 ({mode}): '{user_text[:80]}...'")

        session["history"].append({"role": "user", "text": user_text})
        session["round"] += 1

        # 算法流利度
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

        llm = get_llm_service()
        grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

        ai_text = await llm.chat(topic, user_text, session["history"][:-1], cefr_level, mode=mode)

        session["history"].append({"role": "ai", "text": ai_text})

        grammar_correction = None
        try:
            grammar_result = await grammar_task
            if grammar_result.get("errors"):
                grammar_correction = grammar_result
        except Exception as e:
            logger.warning(f"语法纠错失败: {e}")

        conversation_complete = session["round"] >= MAX_ROUNDS[mode]

        return VoiceChatSpeakResponse(
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
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if converted_path:
            session["user_audios"].append((converted_path, user_text))
        try:
            if tmp_path:
                os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/stream/start")
async def voice_chat_stream_start(
    req: VoiceChatStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = uuid.uuid4().hex[:12]
    topic = req.topic
    mode = req.mode
    cefr_level = req.cefr_level

    # 持久化
    db_session_id = None
    try:
        db_session = ConversationSession(
            user_id=current_user.id, session_uuid=session_id,
            scene=topic, cefr_level=cefr_level, status="active",
        )
        db.add(db_session)
        db.commit()
        db_session_id = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话到 DB 失败: {e}")

    _init_session(session_id, topic, mode, cefr_level, db_session_id)

    openers = _get_openers(mode)
    opener = openers.get(topic, openers[_get_default_topic(mode)])

    llm = get_llm_service()

    async def generate():
        full_text = ""
        try:
            async for token in llm.chat_stream(topic, opener, [], cefr_level, mode=mode):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            _sessions[session_id]["history"].append({"role": "ai", "text": full_text})

            # TTS 预取
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

            tts_url = f"/api/voice-chat/tts/cached/{session_id}/{round_key}"

            translation_task = asyncio.create_task(llm.translate_to_chinese(full_text))
            hint_task = asyncio.create_task(llm.generate_hint(full_text, cefr_level))

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'full_text': full_text, 'tts_url': tts_url})}\n\n"

            async def _wait_tagged(task, tag):
                try:
                    return tag, await task, None
                except Exception as e:
                    return tag, None, e

            pending = [_wait_tagged(translation_task, 'translation'), _wait_tagged(hint_task, 'hint')]
            for coro in asyncio.as_completed(pending):
                tag, result, error = await coro
                if tag == 'translation':
                    if error:
                        logger.warning(f"翻译失败: {error}")
                    elif result:
                        yield f"data: {json.dumps({'type': 'translation', 'data': result})}\n\n"
                elif tag == 'hint':
                    if error:
                        logger.warning(f"提示生成失败: {error}")
                    elif result:
                        try:
                            hint_zh = await llm.translate_to_chinese(result)
                        except Exception:
                            hint_zh = ''
                        yield f"data: {json.dumps({'type': 'hint', 'data': {'en': result, 'zh': hint_zh}})}\n\n"
        except Exception as e:
            logger.error(f"流式 start 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"X-Session-Id": session_id})


@router.post("/stream/speak")
async def voice_chat_stream_speak(
    session_id: str = Form(..., description="会话 ID"),
    audio: UploadFile = File(..., description="用户语音"),
    db: Session = Depends(get_db),
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    mode = session["mode"]
    cefr_level = session["cefr_level"]
    topic = session["topic"]

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

            # 立即存储音频用于发音评分
            session["user_audios"].append((converted_path, user_text))

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
                logger.warning(f"保存用户消息失败: {e}")

            # 算法流利度
            try:
                words = asr_result.get("words", [])
                segments = asr_result.get("segments", [])
                audio_duration = segments[-1].get("end", 5.0) if segments else 5.0
                fluency_algo = assess_algorithmic(user_text, words, audio_duration)
                session["fluency_scores"].append({
                    "text": user_text, "wpm": fluency_algo["wpm"],
                    "pause_frequency": fluency_algo["pause_frequency"],
                    "repetition": fluency_algo["repetition"],
                })
                if db_msg_id:
                    try:
                        db.query(ConversationMessage).filter(
                            ConversationMessage.id == db_msg_id
                        ).update({"fluency_scores": fluency_algo})
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.warning(f"保存流利度失败: {e}")
            except Exception as e:
                logger.warning(f"流利度算法计算失败: {e}")

            # 语法纠错 + LLM 并行
            llm = get_llm_service()
            grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

            full_text = ""
            async for token in llm.chat_stream(
                topic, user_text, session["history"][:-1], cefr_level, mode=mode
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            session["history"].append({"role": "ai", "text": full_text})

            translation_task = asyncio.create_task(llm.translate_to_chinese(full_text))
            hint_task = asyncio.create_task(llm.generate_hint(full_text, cefr_level))

            # 持久化 AI 回复
            try:
                db_sid = session.get("db_session_id")
                if db_sid:
                    db_msg = ConversationMessage(
                        session_id=db_sid, round_number=session["round"],
                        role="assistant", content_text=full_text,
                    )
                    db.add(db_msg)
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"保存 AI 消息失败: {e}")

            conversation_complete = session["round"] >= MAX_ROUNDS[mode]

            # TTS 预取
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

            tts_url = f"/api/voice-chat/tts/cached/{session_id}/{round_key}"
            yield f"data: {json.dumps({'type': 'done', 'full_text': full_text, 'conversation_complete': conversation_complete, 'tts_url': tts_url})}\n\n"

            # 语法 / 翻译 / 提示 并行
            async def _wait_tagged(task, tag):
                try:
                    return tag, await task, None
                except Exception as e:
                    return tag, None, e

            pending = [
                _wait_tagged(grammar_task, 'grammar'),
                _wait_tagged(translation_task, 'translation'),
                _wait_tagged(hint_task, 'hint'),
            ]

            for coro in asyncio.as_completed(pending):
                tag, result, error = await coro
                if tag == 'grammar':
                    if error:
                        logger.warning(f"语法纠错失败: {error}")
                    else:
                        yield f"data: {json.dumps({'type': 'grammar', 'data': result or {'errors': []}})}\n\n"
                        if result and result.get("errors"):
                            session["history"].append({"role": "grammar", "text": result})
                        if db_msg_id and result:
                            try:
                                db.query(ConversationMessage).filter(
                                    ConversationMessage.id == db_msg_id
                                ).update({"grammar_check": result})
                                db.commit()
                            except Exception as e:
                                db.rollback()
                                logger.warning(f"保存语法纠错失败: {e}")
                elif tag == 'translation':
                    if error:
                        logger.warning(f"翻译失败: {error}")
                    elif result:
                        yield f"data: {json.dumps({'type': 'translation', 'data': result})}\n\n"
                elif tag == 'hint':
                    if error:
                        logger.warning(f"提示生成失败: {error}")
                    elif result:
                        try:
                            hint_zh = await llm.translate_to_chinese(result)
                        except Exception:
                            hint_zh = ''
                        yield f"data: {json.dumps({'type': 'hint', 'data': {'en': result, 'zh': hint_zh}})}\n\n"

        except Exception as e:
            logger.error(f"流式 speak 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            try:
                if tmp_path:
                    os.unlink(tmp_path)
            except Exception:
                pass

    return StreamingResponse(generate(), media_type="text/event-stream")


# ========== TTS 端点（完全共享，无 mode 区分） ==========

@router.post("/tts")
async def voice_chat_tts(
    text: str = Form(..., description="要合成的文本"),
    voice: str = Form(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本不能为空")
    try:
        audio_base64 = await _tts_to_base64(text.strip(), voice)
        return {"audio_base64": audio_base64}
    except Exception as e:
        logger.error(f"TTS 失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.get("/tts/stream")
async def voice_chat_tts_stream(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
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
            logger.error(f"流式 TTS 失败: {e}")

    return StreamingResponse(generate(), media_type="audio/mpeg", headers={
        "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff",
    })


@router.get("/tts/cached/{session_id}/{round_key}")
async def voice_chat_tts_cached(session_id: str, round_key: str):
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

    return StreamingResponse(generate(), media_type="audio/mpeg", headers={
        "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff",
    })


# ========== 会话结束 + 评分 ==========

@router.post("/end", response_model=VoiceChatEndResponse)
async def voice_chat_end(
    session_id: str = Form(..., description="会话 ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    mode = session["mode"]
    history = session["history"]
    cefr_level = session["cefr_level"]
    user_audios = session.get("user_audios", [])
    age_group = current_user.age_group

    # 默认值
    pronunciation = []
    text_dimensions = []
    text_dimension_details = []
    dimensions = []
    dimension_details = []
    utterances = []
    overall = 0
    suggestions = ""
    scoring_methodology = ""
    fluency_report = None

    user_messages = [h for h in history if h["role"] == "user"]

    try:
        # 1. 发音评测（共用 wav2vec2）
        if user_audios:
            logger.info(f"开始发音评测，共 {len(user_audios)} 段音频")
            all_dim_scores = {k: [] for k in ("音素准确度", "重音位置", "语调曲线", "连读表现", "节奏感")}

            for wav_path, asr_text in user_audios:
                try:
                    result = await score_audio(wav_path, asr_text, mode="sentence")
                    utterance = {
                        "text": asr_text, "overall": result.get("overall"),
                        "dimensions": result.get("dimensions"), "errors": result.get("errors"),
                        "char_scores": result.get("char_scores"),
                        "analysis_detail": result.get("analysis_detail"),
                    }
                    # scene 模式额外包含可视化数据
                    if mode == "scene":
                        utterance.update({
                            "stress_viz": result.get("stress_viz"),
                            "intonation_viz": result.get("intonation_viz"),
                            "linking_viz": result.get("linking_viz"),
                            "rhythm_viz": result.get("rhythm_viz"),
                        })
                    utterances.append(utterance)
                    for dim in result.get("dimensions", []):
                        key = dim["label"]
                        if key in all_dim_scores:
                            all_dim_scores[key].append(dim["score"])
                except Exception as e:
                    logger.warning(f"单段音频发音评测失败: {e}")
                    continue

            for label, scores in all_dim_scores.items():
                if scores:
                    pronunciation.append({"label": label, "score": round(sum(scores) / len(scores))})

        # 2. LLM 文本/角色评分（按 mode 分支）
        llm = get_llm_service()
        if mode == "scene":
            if len(user_messages) >= 1:
                text_result = await llm.score_conversation(history, cefr_level, age_group)
                text_dimensions = [
                    {"label": "语法正确率", "score": text_result.get("grammar", 75)},
                    {"label": "词汇丰富度", "score": text_result.get("vocabulary", 75)},
                    {"label": "对话参与度", "score": text_result.get("engagement", 75)},
                ]
                text_dimension_details = [
                    {
                        "label": "语法正确率", "score": text_result.get("grammar", 75),
                        "feedback": text_result.get("grammar_feedback", ""),
                        "strengths": text_result.get("grammar_strengths", ""),
                        "weaknesses": text_result.get("grammar_weaknesses", ""),
                    },
                    {
                        "label": "词汇丰富度", "score": text_result.get("vocabulary", 75),
                        "feedback": text_result.get("vocabulary_feedback", ""),
                        "strengths": text_result.get("vocabulary_strengths", ""),
                        "weaknesses": text_result.get("vocabulary_weaknesses", ""),
                    },
                    {
                        "label": "对话参与度", "score": text_result.get("engagement", 75),
                        "feedback": text_result.get("engagement_feedback", ""),
                        "strengths": text_result.get("engagement_strengths", ""),
                        "weaknesses": text_result.get("engagement_weaknesses", ""),
                    },
                ]
                suggestions = text_result.get("suggestions", "")
            else:
                text_dimensions = [
                    {"label": "语法正确率", "score": 0},
                    {"label": "词汇丰富度", "score": 0},
                    {"label": "对话参与度", "score": 0},
                ]
                suggestions = "你还没有开口说话，无法评估你的口语水平。再来一次试试吧！"

            # 综合分 = 语音均分 + 文本均分（按年龄段自适应）
            from app.services.age_adaptive import get_conversation_ratio, get_conversation_text_weights
            pron_weight, text_weight = get_conversation_ratio(age_group)
            text_weights = get_conversation_text_weights(age_group)

            pron_avg = sum(d["score"] for d in pronunciation) / len(pronunciation) if pronunciation else 0
            text_avg = sum(
                d["score"] * text_weights.get(d["label"], 0.33) for d in text_dimensions
            ) if text_dimensions else 0

            if pronunciation and text_dimensions:
                overall = round(pron_avg * pron_weight + text_avg * text_weight)
            elif pronunciation:
                overall = round(pron_avg)
            elif text_dimensions:
                overall = round(text_avg)

            scoring_methodology = (
                f"综合分 = 语音平均分 × {pron_weight:.0%} + 文本平均分 × {text_weight:.0%}\n"
                "语音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感\n"
                "文本评测（LLM 评估）：语法正确率、词汇丰富度、对话参与度"
            )

        else:  # mode == "role"
            if len(user_messages) >= 1:
                rp_result = await llm.score_roleplay(history, cefr_level, age_group)
                dimensions = [
                    {"label": "角色贴合度", "score": rp_result.get("role_fit", 75)},
                    {"label": "场景礼仪", "score": rp_result.get("etiquette", 75)},
                    {"label": "专业术语", "score": rp_result.get("terminology", 75)},
                    {"label": "应对能力", "score": rp_result.get("response", 75)},
                ]
                dimension_details = [
                    {
                        "label": "角色贴合度", "score": rp_result.get("role_fit", 75),
                        "feedback": rp_result.get("role_fit_feedback", ""),
                        "strengths": rp_result.get("role_fit_strengths", ""),
                        "weaknesses": rp_result.get("role_fit_weaknesses", ""),
                    },
                    {
                        "label": "场景礼仪", "score": rp_result.get("etiquette", 75),
                        "feedback": rp_result.get("etiquette_feedback", ""),
                        "strengths": rp_result.get("etiquette_strengths", ""),
                        "weaknesses": rp_result.get("etiquette_weaknesses", ""),
                    },
                    {
                        "label": "专业术语", "score": rp_result.get("terminology", 75),
                        "feedback": rp_result.get("terminology_feedback", ""),
                        "strengths": rp_result.get("terminology_strengths", ""),
                        "weaknesses": rp_result.get("terminology_weaknesses", ""),
                    },
                    {
                        "label": "应对能力", "score": rp_result.get("response", 75),
                        "feedback": rp_result.get("response_feedback", ""),
                        "strengths": rp_result.get("response_strengths", ""),
                        "weaknesses": rp_result.get("response_weaknesses", ""),
                    },
                ]
                suggestions = rp_result.get("suggestions", "")
            else:
                dimensions = [
                    {"label": "角色贴合度", "score": 0}, {"label": "场景礼仪", "score": 0},
                    {"label": "专业术语", "score": 0}, {"label": "应对能力", "score": 0},
                ]
                suggestions = "还没有开口说话，无法评估。再来一次试试吧！"

            from app.services.age_adaptive import get_roleplay_role_weights
            role_weights = get_roleplay_role_weights(age_group)
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

            w = role_weights
            scoring_methodology = (
                f"综合分 = 角色表现加权分 × 60% + 发音均分 × 40%（{age_group}自适应权重）\n"
                f"角色表现（LLM 评估）：角色贴合度({w.get('角色贴合度',0.40):.0%})、"
                f"场景礼仪({w.get('场景礼仪',0.25):.0%})、专业术语({w.get('专业术语',0.20):.0%})、"
                f"应对能力({w.get('应对能力',0.15):.0%})\n"
                "发音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感"
            )

        # 3. 流利度评估
        fluency_scores = session.get("fluency_scores", [])
        if fluency_scores and len(user_messages) >= 1:
            try:
                llm_utterances = []
                for i, fs in enumerate(fluency_scores):
                    context = ""
                    for j in range(len(history)):
                        if history[j].get("role") == "user" and history[j]["text"] == fs["text"]:
                            for k in range(j - 1, -1, -1):
                                if history[k].get("role") in ("ai", "assistant"):
                                    context = history[k]["text"]
                                    break
                            break
                    llm_utterances.append({"round": i + 1, "text": fs["text"], "context": context})

                fluency_llm_result = await llm.score_fluency(
                    llm_utterances, cefr_level, session.get("topic", "")
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
            except Exception as e:
                logger.warning(f"流利度 LLM 评估失败: {e}")
                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = "流利度评估仅供参考，多说多练！"

    except Exception as e:
        logger.error(f"评分失败: {e}")
        overall = 0
        suggestions = "评分服务暂时异常，请稍后重试"

    finally:
        for wav_path, _ in user_audios:
            try:
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
            except Exception:
                pass

        # 持久化对话分数到用户画像
        if mode == "scene":
            try:
                from app.services.profile_updater import profile_updater
                profile_updater.ingest_conversation_scores(
                    current_user.id, pronunciation, text_dimensions,
                    source_id=0, db=db,
                )
                db.commit()
            except Exception as e:
                logger.warning(f"持久化对话分数失败: {e}")

        # 更新 DB 会话评分
        try:
            db_session_id = session.get("db_session_id")
            if db_session_id:
                if mode == "scene":
                    update_fields = {
                        "round_count": session.get("round", 0),
                        "status": "completed",
                        "score_pronunciation": round(sum(d["score"] for d in pronunciation) / len(pronunciation), 2) if pronunciation else None,
                        "score_grammar": next((d["score"] for d in text_dimensions if d["label"] == "语法正确率"), None),
                        "score_vocabulary": next((d["score"] for d in text_dimensions if d["label"] == "词汇丰富度"), None),
                        "score_engagement": next((d["score"] for d in text_dimensions if d["label"] == "对话参与度"), None),
                        "score_overall": overall,
                        "improvement_suggestions": suggestions,
                        "ended_at": func.now(),
                    }
                else:
                    update_fields = {
                        "round_count": session.get("round", 0),
                        "status": "completed",
                        "score_pronunciation": round(sum(d["score"] for d in pronunciation) / len(pronunciation), 2) if pronunciation else None,
                        "score_grammar": next((d["score"] for d in dimensions if d["label"] == "场景礼仪"), None),
                        "score_vocabulary": next((d["score"] for d in dimensions if d["label"] == "专业术语"), None),
                        "score_engagement": next((d["score"] for d in dimensions if d["label"] == "应对能力"), None),
                        "score_overall": overall,
                        "improvement_suggestions": suggestions,
                        "ended_at": func.now(),
                    }
                db.query(ConversationSession).filter(
                    ConversationSession.id == db_session_id
                ).update(update_fields)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"保存会话评分到 DB 失败: {e}")

        if session_id in _sessions:
            del _sessions[session_id]

    return VoiceChatEndResponse(
        overall=overall, mode=mode,
        pronunciation=pronunciation,
        text_dimensions=text_dimensions, text_dimension_details=text_dimension_details,
        dimensions=dimensions, dimension_details=dimension_details,
        suggestions=suggestions, utterances=utterances, transcript=history,
        scoring_methodology=scoring_methodology, fluency=fluency_report,
    )


# ========== 会话列表 ==========

@router.get("/sessions")
async def list_sessions(
    limit: int = 10,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ConversationSession)
        .filter(ConversationSession.user_id == current_user.id)
        .order_by(ConversationSession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "session_uuid": s.session_uuid,
            "scene": s.scene,
            "cefr_level": s.cefr_level,
            "round_count": s.round_count,
            "status": s.status,
            "score_overall": float(s.score_overall) if s.score_overall else None,
            "score_pronunciation": float(s.score_pronunciation) if s.score_pronunciation else None,
            "score_grammar": float(s.score_grammar) if s.score_grammar else None,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        }
        for s in sessions
    ]
