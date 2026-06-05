"""
实时录音 → WhisperX 转录
使用 ffmpeg 录音，然后 WhisperX 转录 + 单词级对齐
"""

import os
import time
import subprocess
import whisperx
import torch

# ============================================================
# 配置
# ============================================================
HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT

MODEL_SIZE = "small"       # tiny/base/small/medium/large-v2/large-v3
DEVICE = "cpu"             # Apple Silicon 用 cpu（ctranslate2 不支持 MPS）
COMPUTE_TYPE = "int8"      # int8 量化，CPU 上速度足够
LANGUAGE = "en"            # 英语，设为 None 自动检测

AUDIO_FILE = "recording.wav"

# ============================================================
# 1. 加载模型（只加载一次）
# ============================================================
print("加载 WhisperX 模型...")
asr_model = whisperx.load_model(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, language=LANGUAGE)
print("模型就绪。\n")

# 预加载对齐模型（英语）
align_model, align_metadata = whisperx.load_align_model(language_code="en", device=DEVICE)

# ============================================================
# 2. 录音
# ============================================================
DURATION = input("录音时长（秒，默认 10）: ").strip()
DURATION = int(DURATION) if DURATION else 10

print(f"\n开始录音 {DURATION} 秒... 请对着麦克风说英语")
print("按 Enter 提前结束录音")
print("=" * 40)

# 使用 ffmpeg 录制（macOS 上 avfoundation 是最简单的设备名）
# 列出设备：ffmpeg -f avfoundation -list_devices true -i ""
subprocess.run(
    [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-i", ":0",           # 默认麦克风
        "-t", str(DURATION),
        "-ac", "1",
        "-ar", "16000",
        AUDIO_FILE,
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print("录音结束。\n")

# ============================================================
# 3. 转录
# ============================================================
print("正在转录...")
t0 = time.time()
result = asr_model.transcribe(AUDIO_FILE, batch_size=8)
print(f"转录完成 ({time.time() - t0:.1f}s)\n")

# ============================================================
# 4. 单词级对齐
# ============================================================
print("正在单词级对齐...")
t0 = time.time()
result = whisperx.align(result["segments"], align_model, align_metadata, AUDIO_FILE, device=DEVICE)
print(f"对齐完成 ({time.time() - t0:.1f}s)\n")

# ============================================================
# 5. 输出
# ============================================================
print("=" * 50)
print("转录结果")
print("=" * 50)

for segment in result["segments"]:
    print(f"\n[{segment['start']:.1f}s → {segment['end']:.1f}s]")
    print(f"  {segment['text'].strip()}")

    if "words" in segment:
        print("\n  单词级时间戳:")
        for w in segment["words"]:
            word_text = w.get("word", w.get("text", "")).strip()
            if not word_text:
                continue
            score = w.get("score", 0)
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"  {word_text:<15s} {w['start']:.2f}s → {w['end']:.2f}s  [{bar}] {score:.2f}")

# 清理
if os.path.exists(AUDIO_FILE):
    os.remove(AUDIO_FILE)
