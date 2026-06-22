"""TTS 语音合成服务 — Edge TTS（微软免费）"""

import io
import logging

logger = logging.getLogger(__name__)

# 可用音色
VOICES = {
    "female": "en-US-JennyNeural",
    "male": "en-US-GuyNeural",
    "female2": "en-US-AriaNeural",
    "male2": "en-US-DavisNeural",
}


async def synthesize_speech(text: str, voice: str = "en-US-JennyNeural") -> bytes:
    """
    将文本转为 MP3 音频流

    Args:
        text: 要合成的英文文本
        voice: Edge TTS 音色名称

    Returns:
        MP3 音频字节流
    """
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if not audio_chunks:
            raise RuntimeError("TTS 生成失败：无音频数据")

        audio_bytes = b"".join(audio_chunks)
        logger.info(f"TTS 合成成功: {len(audio_bytes)} bytes, text='{text[:40]}...'")
        return audio_bytes

    except ImportError:
        raise RuntimeError("Edge TTS 未安装，请执行 pip install edge-tts")