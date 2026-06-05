"""发音评测 API 路由"""

import os
import io
import tempfile
import subprocess
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.pronunciation import PronunciationResponse
from app.services.pronunciation import score_audio

router = APIRouter()
logger = logging.getLogger(__name__)


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV（使用 ffmpeg）"""
    output_path = input_path + "_converted.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         output_path],
        check=True, capture_output=True,
    )
    return output_path


@router.post("/score", response_model=PronunciationResponse)
async def pronunciation_score(
    audio: UploadFile = File(..., description="学习者录音文件（任意格式，后端自动转 WAV）"),
    text: str = Form(..., description="跟读的标准文本"),
):
    """
    发音评测接口

    接收音频 + 标准文本，返回基于 wav2vec2 + GOP 的音素级评分结果。
    支持任意浏览器录音格式（webm, mp4, wav 等），后端自动转码。
    """
    # 参数校验
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本内容不能为空")

    text = text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=422, detail="文本长度不能超过 500 字符")

    # 保存上传的音频到临时文件
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

        logger.info(f"收到发音评测请求: text='{text[:50]}...', audio_size={len(content)} bytes")

        # 转码为 16kHz WAV（浏览器录音通常是 webm）
        converted_path = convert_to_wav(tmp_path)
        logger.info(f"音频转码完成: {os.path.getsize(converted_path)} bytes")

        # 执行发音评测
        result = await score_audio(converted_path, text)
        return PronunciationResponse(**result)

    except subprocess.CalledProcessError as e:
        logger.error(f"音频转码失败: {e.stderr.decode() if e.stderr else str(e)}")
        raise HTTPException(status_code=422, detail="音频格式无法识别，请确认录音正常")
    except RuntimeError as e:
        logger.error(f"模型错误: {e}")
        raise HTTPException(status_code=503, detail=f"模型服务不可用: {str(e)}")
    except Exception as e:
        logger.error(f"发音评测失败: {e}")
        raise HTTPException(status_code=500, detail=f"评测失败: {str(e)}")
    finally:
        # 清理临时文件
        for path in (tmp_path, converted_path):
            try:
                if path:
                    os.unlink(path)
            except Exception:
                pass


@router.post("/reference-audio")
async def get_reference_audio(
    text: str = Form(..., description="标准文本"),
    voice: str = Form(default="en-US-JennyNeural", description="Edge TTS 音色"),
):
    """
    生成标准发音参考音频（Edge TTS）

    返回 MP3 音频流。
    可选音色: en-US-JennyNeural(女), en-US-GuyNeural(男),
             en-US-AriaNeural(女), en-US-DavisNeural(男)
    """
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本不能为空")

    text = text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=422, detail="文本过长")

    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if not audio_chunks:
            raise HTTPException(status_code=500, detail="TTS 生成失败")

        audio_bytes = b"".join(audio_chunks)
        logger.info(f"Edge TTS 生成成功: text='{text[:30]}...', size={len(audio_bytes)} bytes")

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=reference.mp3"},
        )

    except ImportError:
        raise HTTPException(status_code=503, detail="Edge TTS 未安装，请执行 pip install edge-tts")
    except Exception as e:
        logger.error(f"Edge TTS 失败: {e}")
        raise HTTPException(status_code=500, detail=f"参考音频生成失败: {str(e)}")
