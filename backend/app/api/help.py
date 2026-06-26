"""智能客服 API 路由"""

import json
import logging
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.help import ChatRequest, ChatResponse
from app.services.help import help_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_text(
    req: ChatRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """文字客服：发送问题，获取 AI 回复"""
    try:
        result = await help_service.chat(req.message, req.history)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"客服接口异常: {e}")
        return ChatResponse(
            reply="抱歉，我暂时无法处理你的问题。请查看常见问题或联系人工客服 support@lingolab.com。",
            category="tech_issue",
            escalate=True,
        )


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """文字客服（流式）：SSE 逐 token 返回 AI 回复"""
    async def generate():
        try:
            async for token in help_service.chat_stream(req.message, req.history):
                yield f"data: {json.dumps({'content': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"客服流式接口异常: {e}")
            yield f"data: {json.dumps({'content': '抱歉，我暂时无法处理你的问题。请稍后重试。'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(...),
    history: str = "[]",
    current_user: UserProfile = Depends(get_current_user),
):
    """语音客服：上传录音 → Whisper 转写 → AI 回复"""
    try:
        history_list = json.loads(history)
    except json.JSONDecodeError:
        history_list = []

    # 保存临时音频文件
    suffix = ".webm" if audio.filename and audio.filename.endswith(".webm") else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Whisper 转写
        from app.services.asr import get_asr_service
        asr = get_asr_service()
        result = asr.transcribe(tmp_path)
        transcript = result.get("text", "") if isinstance(result, dict) else str(result)
        if not transcript or not transcript.strip():
            return ChatResponse(
                reply="未能识别你的语音，请用文字输入问题。",
                category="tech_issue",
                escalate=False,
            )

        result = await help_service.chat(transcript, history_list)
        result["transcript"] = transcript
        return ChatResponse(**result)
    finally:
        os.unlink(tmp_path)