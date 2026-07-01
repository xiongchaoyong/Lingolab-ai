"""发音评测 API 路由"""

import os
import io
import tempfile
import subprocess
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import UserProfile
from app.schemas.pronunciation import PronunciationResponse, ContentItem, RecordItem
from app.models.pronunciation import PronunciationContent, PronunciationRecord
from app.services.pronunciation import score_audio
from app.services.profile_updater import profile_updater

router = APIRouter()
logger = logging.getLogger(__name__)


def convert_to_wav(input_path: str) -> str:
    """将任意音频格式转为 16kHz 单声道 WAV（使用 ffmpeg）"""
    output_path = input_path + "_converted.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
             output_path],
            check=True, capture_output=True, timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg 未安装，请安装 ffmpeg 后重试")
    return output_path


@router.post("/score", response_model=PronunciationResponse)
async def pronunciation_score(
    audio: UploadFile = File(..., description="学习者录音文件（任意格式，后端自动转 WAV）"),
    text: str = Form(..., description="跟读的标准文本"),
    mode: str = Form(default="word", description="跟读模式：word/sentence"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    发音评测接口

    接收音频 + 标准文本 + 模式，返回基于 wav2vec2 + GOP 的音素级评分结果。
    支持任意浏览器录音格式（webm, mp4, wav 等），后端自动转码。
    综合分按模式加权：单词（音素50%/重音25%/节奏25%），句子（音素40%/重音15%/连读15%/语调15%/节奏15%）。
    """
    # 参数校验
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="文本内容不能为空")

    text = text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=422, detail="文本长度不能超过 500 字符")

    if mode not in ("word", "sentence"):
        raise HTTPException(status_code=422, detail="mode 参数必须为 word 或 sentence")

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
        result = await score_audio(converted_path, text, mode)

        # 持久化分数到用户画像
        try:
            profile_updater.ingest_pronunciation_scores(
                current_user.id, result.get("dimensions", []), source_id=0, db=db
            )
            db.commit()
            logger.info(f"用户 {current_user.username} 发音分数已持久化")
        except Exception as e:
            logger.warning(f"持久化发音分数失败: {e}")

        # 保存评测记录到 pronunciation_records
        try:
            dim_map = {d["label"]: d["score"] for d in result.get("dimensions", [])}
            record = PronunciationRecord(
                user_id=current_user.id,
                content_id=0,  # 自由跟读，无关联内容
                mode=mode,
                overall_score=result["overall"],
                phoneme_score=dim_map.get("音素准确度"),
                stress_score=dim_map.get("重音位置"),
                linking_score=dim_map.get("连读表现"),
                intonation_score=dim_map.get("语调曲线"),
                rhythm_score=dim_map.get("节奏感"),
                error_phonemes=result.get("errors", []),
                correction_advice="; ".join(
                    e["tip"] for e in result.get("errors", []) if e.get("tip")
                ) or None,
            )
            db.add(record)
            db.commit()
            logger.info(f"评测记录已保存: user={current_user.id}, score={result['overall']}")
        except Exception as e:
            db.rollback()
            logger.warning(f"保存评测记录失败: {e}")

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


@router.get("/content", response_model=list[ContentItem])
async def list_content(
    content_type: str = None,
    cefr_level: str = None,
    db: Session = Depends(get_db),
):
    """获取跟读内容库列表，支持按类型和难度筛选"""
    query = db.query(PronunciationContent).filter(PronunciationContent.is_active == 1)
    if content_type:
        query = query.filter(PronunciationContent.content_type == content_type)
    if cefr_level:
        query = query.filter(PronunciationContent.cefr_level == cefr_level)
    items = query.order_by(PronunciationContent.cefr_level, PronunciationContent.id).all()
    return items


@router.get("/records", response_model=list[RecordItem])
async def list_records(
    limit: int = 20,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的评测历史记录"""
    records = (
        db.query(PronunciationRecord)
        .filter(PronunciationRecord.user_id == current_user.id)
        .order_by(PronunciationRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in records:
        content = None
        if r.content_id:
            content = db.query(PronunciationContent).get(r.content_id)
        result.append(RecordItem(
            id=r.id,
            content_id=r.content_id,
            mode=r.mode,
            overall_score=float(r.overall_score),
            phoneme_score=float(r.phoneme_score) if r.phoneme_score else None,
            stress_score=float(r.stress_score) if r.stress_score else None,
            created_at=r.created_at,
            content_title=content.title if content else None,
            content_text=content.content_text if content else None,
        ))
    return result
