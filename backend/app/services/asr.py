"""ASR 语音识别服务 — WhisperX 转录 + 词级时间戳"""

import logging
import whisperx

logger = logging.getLogger(__name__)

# 全局单例
_asr_instance = None


class ASRService:
    """WhisperX 语音转文字服务"""

    def __init__(self, model_size: str = "small", device: str = "cpu"):
        self.device = device
        logger.info(f"加载 WhisperX {model_size} 模型 (device={device})...")
        self.model = whisperx.load_model(model_size, device, compute_type="int8")
        self.align_model, self.align_metadata = whisperx.load_align_model(
            language_code="en", device=device
        )
        logger.info("WhisperX ASR 服务就绪")

    def transcribe(self, audio_path: str) -> dict:
        """
        转录音频为文本

        返回:
            {
                "text": "完整转录文本",
                "segments": [{"text": "...", "start": 0.0, "end": 1.5}, ...],
                "words": [{"word": "hello", "start": 0.1, "end": 0.5, "score": 0.98}, ...],
                "confidence": 0.92
            }
        """
        try:
            result = self.model.transcribe(audio_path, batch_size=1)
            aligned = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio_path,
                device=self.device,
            )

            words = []
            for seg in aligned.get("word_segments", aligned.get("segments", [])):
                if "words" in seg:
                    words.extend(seg["words"])
                elif "word" in seg:
                    words.append(seg)

            confidence = result.get("confidence", 0.0)
            if isinstance(confidence, (list, tuple)):
                confidence = sum(confidence) / len(confidence) if confidence else 0.0

            return {
                "text": " ".join(w.get("word", "").strip() for w in words),
                "segments": aligned.get("segments", []),
                "words": words,
                "confidence": round(float(confidence), 3),
            }
        except Exception as e:
            logger.error(f"WhisperX 转录失败: {e}")
            return {"text": "", "segments": [], "words": [], "confidence": 0.0}


def get_asr_service() -> ASRService:
    """获取全局 ASR 服务单例"""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = ASRService()
    return _asr_instance