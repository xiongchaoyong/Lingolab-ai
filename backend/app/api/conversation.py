"""语音对话 API 路由 — ASR → LLM → TTS 管线"""

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

from app.schemas.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationSpeakResponse,
    ConversationEndResponse,
)
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.tts import synthesize_speech
from app.services.pronunciation import score_audio

router = APIRouter()
logger = logging.getLogger(__name__)

# 内存会话存储（生产环境应迁移至 Redis）
_sessions: dict[str, dict] = {}

MAX_CONVERSATION_ROUNDS = 6


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


@router.post("/start", response_model=ConversationStartResponse)
async def conversation_start(req: ConversationStartRequest):
    """
    开始新对话

    立即返回 session_id + AI 开场白文本，语音通过 /tts 接口异步获取。
    """
    session_id = uuid.uuid4().hex[:12]
    scene = req.scene
    cefr_level = req.cefr_level

    # 初始化会话
    _sessions[session_id] = {
        "scene": scene,
        "cefr_level": cefr_level,
        "history": [],
        "round": 0,
        "user_audios": [],  # (wav_path, asr_text) 用于发音评分
    }

    # 生成 AI 开场白（不同场景使用不同的开场提示）
    scene_openers = {
        "self_intro": "Greet the user and ask them to introduce themselves.",
        "directions": "You are lost. Ask the user for directions to a nearby place.",
        "shopping": "Welcome the customer and ask what they are looking for.",
        "restaurant": "Greet the customer and ask if they have a reservation.",
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
        converted_path = _convert_to_wav(tmp_path)

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
async def conversation_stream_start(req: ConversationStartRequest):
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
    }

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
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'full_text': full_text})}\n\n"
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

            # 流式 LLM
            llm = get_llm_service()
            full_text = ""
            async for token in llm.chat_stream(
                scene, user_text, session["history"][:-1], cefr_level
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            session["history"].append({"role": "ai", "text": full_text})
            conversation_complete = session["round"] >= MAX_CONVERSATION_ROUNDS
            yield f"data: {json.dumps({'type': 'done', 'full_text': full_text, 'conversation_complete': conversation_complete})}\n\n"

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


@router.post("/end", response_model=ConversationEndResponse)
async def conversation_end(
    session_id: str = Form(..., description="会话 ID"),
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
    overall = 0
    suggestions = ""

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
                    for dim in result.get("dimensions", []):
                        key = dim["label"]
                        if key in all_dim_scores:
                            all_dim_scores[key].append(dim["score"])
                except Exception as e:
                    logger.warning(f"单段音频发音评测失败: {e}")
                    continue

            # 平均各维度
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
            suggestions = text_result.get("suggestions", "")
        else:
            # 用户未发言，各项评分归零
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

    return ConversationEndResponse(
        overall=overall,
        pronunciation=pronunciation,
        text_dimensions=text_dimensions,
        suggestions=suggestions,
    )