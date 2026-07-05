"""语法纠错 API 路由 — 文本/语音输入 → 语法纠错 + 润色"""

import os
import tempfile
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.schemas.grammar import GrammarCorrectResponse, GrammarError
from app.services.asr import get_asr_service
from app.services.llm import get_llm_service
from app.services.audio_utils import convert_to_wav

router = APIRouter()
logger = logging.getLogger(__name__)


def _deduplicate_and_apply(raw_errors: list, text: str) -> tuple:
    """
    去重 + 从原文逐词替换构造修正版。

    策略：
    1. 按 original 在原句中首次出现的位置排序
    2. 同一个 original 去重（只保留一条）
    3. 从后往前替换（避免索引偏移），一次只替换 original 在原句中的第一次出现
    4. 保证修正文本的空格和原句完全一致
    """
    if not raw_errors:
        return [], text

    # 去重：同一个 original 保留第一条
    seen = set()
    unique = []
    for e in raw_errors:
        orig = (e.get("original") or "").strip()
        if orig and orig not in seen:
            seen.add(orig)
            unique.append(e)

    # 按 original 在原句中的位置排序
    def find_pos(e):
        orig = (e.get("original") or "").strip()
        idx = text.find(orig)
        return idx if idx >= 0 else 999999

    unique.sort(key=find_pos)

    # 从后往前替换，保证索引稳定
    corrected = text
    for e in unique:
        orig = (e.get("original") or "").strip()
        corr = (e.get("correction") or "").strip()
        if orig and orig in corrected:
            corrected = corrected.replace(orig, corr, 1)

    formatted = [GrammarError(**e) for e in unique]
    return formatted, corrected


@router.post("/correct", response_model=GrammarCorrectResponse)
async def grammar_correct(
    text: str = Form(..., description="待纠错的英文文本"),
    cefr_level: str = Form(default="B1", description="CEFR 等级"),
):
    """语法纠错与润色 — 文本输入"""
    text = text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="文本不能为空")
    if len(text) > 1000:
        raise HTTPException(status_code=422, detail="文本过长，请控制在 1000 字符以内")

    try:
        llm = get_llm_service()
        result = await llm.correct_grammar(text, cefr_level)
        raw_errors = result.get("errors", []) if isinstance(result.get("errors"), list) else []
        errors, corrected = _deduplicate_and_apply(raw_errors, text)

        return GrammarCorrectResponse(
            original_text=text,
            corrected_text=corrected,
            errors=errors,
            polished_version=result.get("polished_version", ""),
            suggestions=result.get("suggestions", []),
        )
    except Exception as e:
        logger.error(f"语法纠错失败: {e}")
        raise HTTPException(status_code=500, detail=f"语法纠错服务异常: {str(e)}")


@router.post("/correct/voice", response_model=GrammarCorrectResponse)
async def grammar_correct_voice(
    audio: UploadFile = File(..., description="用户语音"),
    cefr_level: str = Form(default="B1", description="CEFR 等级"),
):
    """语法纠错与润色 — 语音输入"""
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

        asr = get_asr_service()
        asr_result = asr.transcribe(converted_path)
        user_text = asr_result.get("text", "").strip()

        if not user_text:
            return GrammarCorrectResponse(
                original_text="(未识别到语音)",
                corrected_text="(未识别到语音)",
                errors=[],
                polished_version="(未识别到语音)",
                suggestions=["请重新录音，确保麦克风正常工作且环境安静"],
            )

        logger.info(f"语法纠错(语音) ASR: '{user_text[:80]}...'")

        llm = get_llm_service()
        result = await llm.correct_grammar(user_text, cefr_level)
        raw_errors = result.get("errors", []) if isinstance(result.get("errors"), list) else []
        errors, corrected = _deduplicate_and_apply(raw_errors, user_text)

        return GrammarCorrectResponse(
            original_text=user_text,
            corrected_text=corrected,
            errors=errors,
            polished_version=result.get("polished_version", ""),
            suggestions=result.get("suggestions", []),
        )

    except Exception as e:
        logger.error(f"语法纠错(语音)失败: {e}")
        raise HTTPException(status_code=500, detail=f"语法纠错服务异常: {str(e)}")
    finally:
        for path in (tmp_path, converted_path):
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass
