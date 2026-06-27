"""语音对话 API 路由 — ASR → LLM → TTS 管线"""

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
from app.schemas.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationSpeakResponse,
    ConversationEndResponse,
)
from app.models.conversation import ConversationSession, ConversationMessage
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

MAX_CONVERSATION_ROUNDS = 10


async def _tts_to_base64(text: str, voice: str = "en-US-JennyNeural") -> str:
    """生成 TTS 音频并返回 base64 编码"""
    audio_bytes = await synthesize_speech(text, voice)
    return base64.b64encode(audio_bytes).decode("utf-8")


@router.post("/start", response_model=ConversationStartResponse)
async def conversation_start(
    req: ConversationStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    开始新对话

    立即返回 session_id + AI 开场白文本，语音通过 /tts 接口异步获取。
    """
    session_id = uuid.uuid4().hex[:12]
    scene = req.scene
    cefr_level = req.cefr_level

    # 初始化内存会话
    _sessions[session_id] = {
        "scene": scene,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],  # (wav_path, asr_text) 用于发音评分
        "fluency_scores": [],  # 每轮流利度算法评分
        "tts_cache": {},  # TTS 预取缓存 {round_key: {"chunks": [...], "done": bool}}
    }

    # 持久化到 DB
    try:
        db_session = ConversationSession(
            user_id=current_user.id,
            session_uuid=session_id,
            scene=scene,
            cefr_level=cefr_level,
            status="active",
        )
        db.add(db_session)
        db.commit()
        _sessions[session_id]["db_session_id"] = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话到 DB 失败: {e}")

    # 生成 AI 开场白（不同场景使用不同的开场提示）
    scene_openers = {
        "self_intro": "Greet the user and ask them to introduce themselves.",
        "directions": "You are lost. Ask the user for directions to a nearby place.",
        "shopping": "Welcome the customer and ask what they are looking for.",
        "restaurant": "Greet the customer and ask if they have a reservation.",
        "hotel": "Greet the guest arriving at the hotel and ask if they have a reservation.",
        "airport": "Greet the passenger at the check-in counter and ask for their destination.",
        "hospital": "Greet the patient and ask what symptoms they are experiencing.",
        "school": "Greet the new classmate and ask about their major and interests.",
    }
    opener = scene_openers.get(scene, scene_openers["self_intro"])

    llm = get_llm_service()
    ai_text = await llm.chat(
        scene=scene,
        user_text=opener,
        history=[],
        cefr_level=cefr_level,
    )

    # 记录 AI 消息
    _sessions[session_id]["history"].append({"role": "ai", "text": ai_text})

    logger.info(f"对话开始: session={session_id}, scene={scene}, level={cefr_level}")
    return ConversationStartResponse(
        session_id=session_id,
        ai_text=ai_text,
        ai_audio_base64="",  # 语音通过 /tts 异步获取
    )


@router.post("/speak", response_model=ConversationSpeakResponse)
async def conversation_speak(
    session_id: str = Form(..., description="会话 ID"),
    scene: str = Form(default="self_intro", description="场景标识"),
    audio: UploadFile = File(..., description="用户语音"),
):
    """
    用户说话

    流程：音频转写(ASR) → LLM 生成回复 → TTS 合成语音
    返回：转写文本 + AI 回复文本 + AI 语音 base64
    """
    # 校验会话
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    cefr_level = session["cefr_level"]

    # 保存用户音频
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
            return ConversationSpeakResponse(
                user_text="(未识别到语音)",
                ai_text="I didn't catch that. Could you say it again?",
                ai_audio_base64="",
            )

        logger.info(f"ASR 转写: '{user_text[:80]}...'")

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
            logger.debug(f"流利度算法评分: overall={fluency_algo['overall']}/65")
        except Exception as e:
            logger.warning(f"流利度算法计算失败: {e}")

        # LLM 生成回复
        llm = get_llm_service()
        ai_text = await llm.chat(
            scene=scene,
            user_text=user_text,
            history=session["history"][:-1],  # 不包含当前用户消息
            cefr_level=cefr_level,
        )

        # 记录 AI 消息
        session["history"].append({"role": "ai", "text": ai_text})

        # 检查是否对话结束
        conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS

        return ConversationSpeakResponse(
            user_text=user_text,
            ai_text=ai_text,
            ai_audio_base64="",  # 语音通过 /tts 异步获取
            conversation_complete=conversation_complete,
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"音频转码失败: {e.stderr.decode() if e.stderr else str(e)}")
        raise HTTPException(status_code=422, detail="音频格式无法识别")
    except Exception as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        # 保留 WAV 文件用于发音评分，只删除原始上传文件
        if converted_path:
            session["user_audios"].append((converted_path, user_text))
        try:
            if tmp_path:
                os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/stream/start")
async def conversation_stream_start(
    req: ConversationStartRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    流式开始新对话 — SSE 逐 token 返回 AI 开场白
    """
    session_id = uuid.uuid4().hex[:12]
    scene = req.scene
    cefr_level = req.cefr_level

    _sessions[session_id] = {
        "scene": scene,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],  # (wav_path, asr_text) 用于发音评分
        "fluency_scores": [],  # 每轮流利度算法评分
        "tts_cache": {},  # TTS 预取缓存
    }

    # 持久化到 DB
    try:
        db_session = ConversationSession(
            user_id=current_user.id,
            session_uuid=session_id,
            scene=scene,
            cefr_level=cefr_level,
            status="active",
        )
        db.add(db_session)
        db.commit()
        _sessions[session_id]["db_session_id"] = db_session.id
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话到 DB 失败: {e}")

    scene_openers = {
        "self_intro": "Greet the user and ask them to introduce themselves.",
        "directions": "You are lost. Ask the user for directions to a nearby place.",
        "shopping": "Welcome the customer and ask what they are looking for.",
        "restaurant": "Greet the customer and ask if they have a reservation.",
    }
    opener = scene_openers.get(scene, scene_openers["self_intro"])

    llm = get_llm_service()

    async def generate():
        full_text = ""
        try:
            async for token in llm.chat_stream(scene, opener, [], cefr_level):
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

            tts_url = f"/api/conversation/tts/cached/{session_id}/{round_key}"
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'full_text': full_text, 'tts_url': tts_url})}\n\n"
        except Exception as e:
            logger.error(f"流式 start 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/stream/speak")
async def conversation_stream_speak(
    session_id: str = Form(..., description="会话 ID"),
    scene: str = Form(default="self_intro", description="场景标识"),
    audio: UploadFile = File(..., description="用户语音"),
    db: Session = Depends(get_db),
):
    """
    流式对话 — ASR 转写后 SSE 逐 token 返回 AI 回复
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

    # 先保存和转码音频（同步操作，无法流式）
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
            # ASR 转写
            asr = get_asr_service()
            asr_result = asr.transcribe(converted_path)
            user_text = asr_result.get("text", "").strip()

            if not user_text:
                yield f"data: {json.dumps({'type': 'asr', 'text': '(未识别到语音)'})}\n\n"
                yield f'data: {{"type": "done", "full_text": "I didn\'t catch that. Could you say it again?"}}\n\n'
                return

            # 发送 ASR 结果
            yield f"data: {json.dumps({'type': 'asr', 'text': user_text})}\n\n"

            session["history"].append({"role": "user", "text": user_text})
            session["round"] += 1

            # 持久化用户消息
            db_msg_id = None
            try:
                db_sid = session.get("db_session_id")
                if db_sid:
                    db_msg = ConversationMessage(
                        session_id=db_sid,
                        round_number=session["round"],
                        role="user",
                        content_text=user_text,
                    )
                    db.add(db_msg)
                    db.commit()
                    db.refresh(db_msg)
                    db_msg_id = db_msg.id
            except Exception as e:
                db.rollback()
                logger.warning(f"保存用户消息失败: {e}")

            # 算法流利度计算（维度1-3，静默存储）
            fluency_data = None
            try:
                words = asr_result.get("words", [])
                segments = asr_result.get("segments", [])
                audio_duration = segments[-1].get("end", 5.0) if segments else 5.0
                fluency_algo = assess_algorithmic(user_text, words, audio_duration)
                fluency_data = {
                    "text": user_text,
                    "wpm": fluency_algo["wpm"],
                    "pause_frequency": fluency_algo["pause_frequency"],
                    "repetition": fluency_algo["repetition"],
                }
                session["fluency_scores"].append(fluency_data)

                # 持久化流利度到 conversation_messages
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

            # 语法纠错（后台并行，与 LLM 回复同时进行，不增加延迟）
            llm = get_llm_service()
            grammar_task = asyncio.create_task(llm.correct_grammar(user_text, cefr_level))

            # 流式 LLM
            full_text = ""
            async for token in llm.chat_stream(
                scene, user_text, session["history"][:-1], cefr_level
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            session["history"].append({"role": "ai", "text": full_text})

            # 持久化 AI 回复
            try:
                db_sid = session.get("db_session_id")
                if db_sid:
                    db_msg = ConversationMessage(
                        session_id=db_sid,
                        round_number=session["round"],
                        role="assistant",
                        content_text=full_text,
                    )
                    db.add(db_msg)
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"保存 AI 消息失败: {e}")
            conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS

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

            tts_url = f"/api/conversation/tts/cached/{session_id}/{round_key}"
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

        except Exception as e:
            logger.error(f"流式 speak 失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # 保留 WAV 用于发音评分，删除原始文件
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
async def conversation_tts(
    text: str = Form(..., description="要合成的文本"),
    voice: str = Form(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
    """
    文本转语音（独立接口，前端异步调用）

    返回 { audio_base64: "..." }
    """
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本不能为空")

    try:
        audio_base64 = await _tts_to_base64(text.strip(), voice)
        return {"audio_base64": audio_base64}
    except Exception as e:
        logger.error(f"TTS 失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.get("/tts/stream")
async def conversation_tts_stream(
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
            logger.error(f"流式 TTS 失败: {e}")

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/tts/cached/{session_id}/{round_key}")
async def conversation_tts_cached(session_id: str, round_key: str):
    """
    获取预取的 TTS 音频缓存 — 后台 Edge TTS 调用完成后流式返回

    与 /tts/stream 不同，此端点不发起新的 TTS 调用，
    而是返回 SSE 流式对话期间后台预取的音频缓存。
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
            # 返回已缓存但未发送的 chunk
            while idx < len(cache["chunks"]):
                yield cache["chunks"][idx]
                idx += 1
            if cache["done"]:
                break
            await asyncio.sleep(0.05)  # 等待后台任务写入更多 chunk

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/end", response_model=ConversationEndResponse)
async def conversation_end(
    session_id: str = Form(..., description="会话 ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    结束对话并评分 — 双层评分体系

    1. 语音维度：wav2vec2 对每段用户音频评测五维（音素准确度/重音/语调/连读/节奏）
    2. 文本维度：LLM 对对话文本评测三维（语法/词汇/参与度）
    3. 综合分 = 语音均分 × 0.5 + 文本均分 × 0.5
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _sessions[session_id]
    history = session["history"]
    cefr_level = session["cefr_level"]
    user_audios = session.get("user_audios", [])

    # 默认值
    pronunciation = []
    text_dimensions = []
    text_dimension_details = []
    utterances = []
    overall = 0
    suggestions = ""
    scoring_methodology = ""
    fluency_report = None

    # 统计用户实际发言次数
    user_messages = [h for h in history if h["role"] == "user"]

    try:
        # 1. 语音评测：对每段用户音频调用 wav2vec2
        if user_audios:
            logger.info(f"开始发音评测，共 {len(user_audios)} 段音频")
            all_dim_scores = {k: [] for k in ("音素准确度", "重音位置", "语调曲线", "连读表现", "节奏感")}

            for wav_path, asr_text in user_audios:
                try:
                    result = await score_audio(wav_path, asr_text, mode="sentence")
                    # 保留完整结果到 utterances
                    utterances.append({
                        "text": asr_text,
                        "overall": result.get("overall"),
                        "dimensions": result.get("dimensions"),
                        "errors": result.get("errors"),
                        "char_scores": result.get("char_scores"),
                        "analysis_detail": result.get("analysis_detail"),
                        "stress_viz": result.get("stress_viz"),
                        "intonation_viz": result.get("intonation_viz"),
                        "linking_viz": result.get("linking_viz"),
                        "rhythm_viz": result.get("rhythm_viz"),
                    })
                    # 累加维度分数用于平均
                    for dim in result.get("dimensions", []):
                        key = dim["label"]
                        if key in all_dim_scores:
                            all_dim_scores[key].append(dim["score"])
                except Exception as e:
                    logger.warning(f"单段音频发音评测失败: {e}")
                    continue

            # 平均各维度（简化版，向后兼容）
            for label, scores in all_dim_scores.items():
                if scores:
                    pronunciation.append({
                        "label": label,
                        "score": round(sum(scores) / len(scores)),
                    })

            if pronunciation:
                logger.info(f"发音评测完成: {pronunciation}")

        # 2. 文本评测：LLM 评分
        if len(user_messages) >= 1:
            llm = get_llm_service()
            text_result = await llm.score_conversation(history, cefr_level)
            text_dimensions = [
                {"label": "语法正确率", "score": text_result.get("grammar", 75)},
                {"label": "词汇丰富度", "score": text_result.get("vocabulary", 75)},
                {"label": "对话参与度", "score": text_result.get("engagement", 75)},
            ]
            # 详细版文本维度
            text_dimension_details = [
                {
                    "label": "语法正确率",
                    "score": text_result.get("grammar", 75),
                    "feedback": text_result.get("grammar_feedback", ""),
                    "strengths": text_result.get("grammar_strengths", ""),
                    "weaknesses": text_result.get("grammar_weaknesses", ""),
                },
                {
                    "label": "词汇丰富度",
                    "score": text_result.get("vocabulary", 75),
                    "feedback": text_result.get("vocabulary_feedback", ""),
                    "strengths": text_result.get("vocabulary_strengths", ""),
                    "weaknesses": text_result.get("vocabulary_weaknesses", ""),
                },
                {
                    "label": "对话参与度",
                    "score": text_result.get("engagement", 75),
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

        # 3. 综合分 = 语音均分 × 0.5 + 文本均分 × 0.5
        pron_avg = sum(d["score"] for d in pronunciation) / len(pronunciation) if pronunciation else 0
        text_avg = sum(d["score"] for d in text_dimensions) / len(text_dimensions) if text_dimensions else 0

        if pronunciation and text_dimensions:
            overall = round(pron_avg * 0.5 + text_avg * 0.5)
        elif pronunciation:
            overall = round(pron_avg)
        elif text_dimensions:
            overall = round(text_avg)

        # 4. 评分方法论说明
        scoring_methodology = (
            "综合分 = 语音平均分 × 50% + 文本平均分 × 50%\n"
            "语音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感\n"
            "文本评测（LLM 评估）：语法正确率、词汇丰富度、对话参与度"
        )

        # 5. 流利度评估（SRS 3.3.3）
        fluency_scores = session.get("fluency_scores", [])
        if fluency_scores and len(user_messages) >= 1:
            try:
                # 构建 LLM 评估的输入
                llm_utterances = []
                for i, fs in enumerate(fluency_scores):
                    # 获取上下文（前一轮 AI 消息）
                    context = ""
                    for j in range(len(history)):
                        if history[j].get("role") == "user" and history[j]["text"] == fs["text"]:
                            # 向前找最近的 AI 消息（跳过 grammar 条目）
                            for k in range(j - 1, -1, -1):
                                if history[k].get("role") in ("ai", "assistant"):
                                    context = history[k]["text"]
                                    break
                            break
                    llm_utterances.append({
                        "round": i + 1,
                        "text": fs["text"],
                        "context": context,
                    })

                # LLM 评估维度 4-5
                llm = get_llm_service()
                fluency_llm_result = await llm.score_fluency(
                    llm_utterances, cefr_level, session.get("scene", "")
                )

                # 合并算法 + LLM 结果
                llm_rounds = fluency_llm_result.get("rounds", [])
                for i, fs in enumerate(fluency_scores):
                    if i < len(llm_rounds):
                        fs["llm"] = {
                            "grammar": llm_rounds[i].get("grammar", {"score": 15, "errors": [], "max": 20}),
                            "relevance": llm_rounds[i].get("relevance", {"score": 10, "max": 15, "note": ""}),
                        }

                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = fluency_llm_result.get("overall_suggestions", "")
                logger.info(f"流利度评估完成: overall={fluency_report['overall']}/100, grade={fluency_report['grade']}")
            except Exception as e:
                logger.warning(f"流利度 LLM 评估失败，仅返回算法评分: {e}")
                # 仅返回算法评分
                fluency_report = aggregate_fluency(fluency_scores)
                fluency_report["suggestions"] = "流利度评估仅供参考，多说多练！"

    except Exception as e:
        logger.error(f"对话评分失败: {e}")
        pronunciation = []
        text_dimensions = [
            {"label": "语法正确率", "score": 0},
            {"label": "词汇丰富度", "score": 0},
            {"label": "对话参与度", "score": 0},
        ]
        overall = 0
        suggestions = "评分服务暂时异常，请稍后重试"

    finally:
        # 清理音频文件
        for wav_path, _ in user_audios:
            try:
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
            except Exception:
                pass
        # 清理会话
        if session_id in _sessions:
            del _sessions[session_id]

    # 持久化对话分数到用户画像
    try:
        from app.services.profile_updater import profile_updater
        profile_updater.ingest_conversation_scores(
            current_user.id, pronunciation, text_dimensions,
            source_id=0, db=db,
        )
        db.commit()
        logger.info(f"用户 {current_user.username} 对话分数已持久化")
    except Exception as e:
        logger.warning(f"持久化对话分数失败: {e}")

    # 更新 DB 会话评分
    try:
        db_session_id = session.get("db_session_id")
        if db_session_id:
            db.query(ConversationSession).filter(
                ConversationSession.id == db_session_id
            ).update({
                "round_count": session.get("round", 0),
                "status": "completed",
                "score_pronunciation": round(sum(d["score"] for d in pronunciation) / len(pronunciation), 2) if pronunciation else None,
                "score_grammar": next((d["score"] for d in text_dimensions if d["label"] == "语法正确率"), None),
                "score_vocabulary": next((d["score"] for d in text_dimensions if d["label"] == "词汇丰富度"), None),
                "score_engagement": next((d["score"] for d in text_dimensions if d["label"] == "对话参与度"), None),
                "score_overall": overall,
                "improvement_suggestions": suggestions,
                "ended_at": func.now(),
            })
            db.commit()
            logger.info(f"会话 {session_id} 评分已保存到 DB")
    except Exception as e:
        db.rollback()
        logger.warning(f"保存会话评分到 DB 失败: {e}")

    return ConversationEndResponse(
        overall=overall,
        pronunciation=pronunciation,
        text_dimensions=text_dimensions,
        suggestions=suggestions,
        utterances=utterances,
        transcript=history,
        text_dimension_details=text_dimension_details,
        scoring_methodology=scoring_methodology,
        fluency=fluency_report,
    )


@router.get("/sessions")
async def list_sessions(
    limit: int = 10,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的对话历史"""
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