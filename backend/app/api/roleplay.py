"""角色扮演 API 路由 — 复用 ASR → LLM(角色Prompt) → TTS 管线"""

import os
import io
import base64
import uuid
import tempfile
import subprocess
import logging

import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

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
}

# 角色中文名
ROLE_NAMES = {
    "interviewee": "面试者",
    "waiter": "服务员",
    "guide": "导游",
}


def _convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV"""
    output_path = input_path + "_converted.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         output_path],
        check=True, capture_output=True,
    )
    return output_path


async def _tts_to_base64(text: str, voice: str = "en-US-JennyNeural") -> str:
    """生成 TTS 音频并返回 base64 编码"""
    audio_bytes = await synthesize_speech(text, voice)
    return base64.b64encode(audio_bytes).decode("utf-8")


@router.post("/start", response_model=RoleplayStartResponse)
async def roleplay_start(req: RoleplayStartRequest):
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
    }

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
        converted_path = _convert_to_wav(tmp_path)

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

        # LLM 角色回复
        llm = get_llm_service()
        ai_text = await llm.chat_roleplay(
            role=role,
            user_text=user_text,
            history=session["history"][:-1],
            cefr_level=cefr_level,
        )

        # 记录 AI 消息
        session["history"].append({"role": "ai", "text": ai_text})

        conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS

        return RoleplaySpeakResponse(
            user_text=user_text,
            ai_text=ai_text,
            ai_audio_base64="",
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
async def roleplay_stream_start(req: RoleplayStartRequest):
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
    }

    opener = ROLE_OPENERS.get(role, ROLE_OPENERS["interviewee"])
    llm = get_llm_service()

    async def generate():
        full_text = ""
        try:
            async for token in llm.chat_roleplay_stream(role, opener, [], cefr_level):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            _sessions[session_id]["history"].append({"role": "ai", "text": full_text})
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'full_text': full_text})}\n\n"
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
        converted_path = _convert_to_wav(tmp_path)
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

            llm = get_llm_service()
            full_text = ""
            async for token in llm.chat_roleplay_stream(
                role, user_text, session["history"][:-1], cefr_level
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            session["history"].append({"role": "ai", "text": full_text})
            conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS
            yield f"data: {json.dumps({'type': 'done', 'full_text': full_text, 'conversation_complete': conversation_complete})}\n\n"

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


@router.post("/end", response_model=RoleplayEndResponse)
async def roleplay_end(
    session_id: str = Form(..., description="会话 ID"),
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

        # 3. 综合分
        role_avg = sum(d["score"] for d in dimensions) / len(dimensions) if dimensions else 0
        pron_avg = sum(d["score"] for d in pronunciation) / len(pronunciation) if pronunciation else 0

        if dimensions and pronunciation:
            overall = round(role_avg * 0.6 + pron_avg * 0.4)
        elif dimensions:
            overall = round(role_avg)
        elif pronunciation:
            overall = round(pron_avg)

        scoring_methodology = (
            "综合分 = 角色表现均分 × 60% + 发音均分 × 40%\n"
            "角色表现（LLM 评估）：角色贴合度、场景礼仪、专业术语、应对能力\n"
            "发音评测（wav2vec2 + GOP 算法）：音素准确度、重音位置、语调曲线、连读表现、节奏感"
        )

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
    )