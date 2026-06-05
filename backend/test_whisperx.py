"""
WhisperX 功能测试脚本
测试内容：模型加载、语音转文字、单词级时间对齐

使用方法:
  # 方式1: 设置 HuggingFace 镜像（国内推荐）
  export HF_ENDPOINT=https://hf-mirror.com
  python3 test_whisperx.py

  # 方式2: 挂代理
  export HTTP_PROXY=http://127.0.0.1:7890
  export HTTPS_PROXY=http://127.0.0.1:7890
  python3 test_whisperx.py
"""

import os
import time
import torch

# 如果没有手动设置 HF_ENDPOINT，自动使用国内镜像
# 如果你的网络可以直接访问 huggingface.co，注释掉下面这行
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    print("已自动设置 HF_ENDPOINT=https://hf-mirror.com（国内镜像）")

# ============================================================
# 1. 环境检查
# ============================================================
print("=" * 50)
print("1. 环境检查")
print("=" * 50)

print(f"Python 版本: {__import__('platform').python_version()}")
print(f"PyTorch 版本: {torch.__version__}")
print(f"MPS (Metal) 可用: {torch.backends.mps.is_available()}")
print(f"MPS 已构建: {torch.backends.mps.is_built()}")

# faster-whisper(ctranslate2) 不支持 MPS，Apple Silicon 用 CPU + int8
# M4 的 CPU 性能极好，int8 量化下 small 模型转录速度 ~实时
device = "cpu"
compute_type = "int8"
print(f"使用设备: {device}（Apple Silicon）")
print(f"计算精度: {compute_type}")

# ============================================================
# 2. 下载并加载模型
# ============================================================
print()
print("=" * 50)
print("2. 加载 WhisperX 模型")
print("=" * 50)

import whisperx

# 选择合适的模型大小
# tiny / base / small / medium / large-v2 / large-v3
MODEL_SIZE = "small"  # 新手推荐 small，速度快且效果不错

print(f"模型大小: {MODEL_SIZE}")
print("正在加载模型（首次会自动下载）...")

t_start = time.time()
asr_model = whisperx.load_model(
    MODEL_SIZE,
    device=device,
    compute_type=compute_type,
    language="en",  # 英语，也可设为 None 自动检测
)
print(f"模型加载完成，耗时 {time.time() - t_start:.1f}s")

# ============================================================
# 3. 语音转文字（ASR）
# ============================================================
print()
print("=" * 50)
print("3. 语音转文字测试")
print("=" * 50)

AUDIO_FILE = "test_audio.wav"
if not os.path.exists(AUDIO_FILE):
    print("生成测试音频...")
    import subprocess
    # 用 macOS say 合成语音
    subprocess.run(
        ["say", "The quick brown fox jumps over the lazy dog", "-o", "test_audio.aiff"],
        check=True,
    )
    # 转成 16kHz mono wav（WhisperX 要求 16kHz）
    subprocess.run(
        ["ffmpeg", "-y", "-i", "test_audio.aiff", "-ac", "1", "-ar", "16000", AUDIO_FILE],
        check=True, capture_output=True,
    )
    os.remove("test_audio.aiff")
    print(f"测试音频已生成: {AUDIO_FILE}")

# 执行转录
print("正在转录...")
t_start = time.time()
result = asr_model.transcribe(AUDIO_FILE, batch_size=8)
transcribe_time = time.time() - t_start
print(f"转录完成，耗时 {transcribe_time:.1f}s")

# 打印结果
print(f"\n--- 转录文本 ---")
for segment in result["segments"]:
    print(f"[{segment['start']:6.2f}s → {segment['end']:6.2f}s] {segment['text'].strip()}")

# ============================================================
# 4. 单词级时间对齐（可选）
# ============================================================
print()
print("=" * 50)
print("4. 单词级时间对齐")
print("=" * 50)

try:
    print("正在加载对齐模型（首次会自动下载）...")
    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device=device,
    )
    print("正在执行单词级对齐...")
    t_start = time.time()
    result_aligned = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        AUDIO_FILE,
        device=device,
    )
    align_time = time.time() - t_start
    print(f"对齐完成，耗时 {align_time:.1f}s")

    # 打印单词级时间戳
    print(f"\n--- 单词级时间对齐 ---")
    for word_info in result_aligned.get("word_segments", result_aligned["segments"]):
        if "word" in word_info:
            # 新版返回格式
            print(f"  {word_info['word']:<15s}  {word_info['start']:.2f}s — {word_info['end']:.2f}s  (置信度: {word_info.get('score', 0):.2f})")
        else:
            # 旧版返回格式
            for word in word_info.get("words", []):
                w = word.get("word", word.get("text", "")).strip()
                if w:
                    print(f"  {w:<15s}  {word['start']:.2f}s — {word['end']:.2f}s  (置信度: {word.get('score', 0):.2f})")
except ImportError:
    print("单词对齐功能需要额外依赖（phonemizer等），请先安装: pip install phonemizer")
except Exception as e:
    print(f"对齐失败: {e}")

# ============================================================
# 5. 总结
# ============================================================
print()
print("=" * 50)
print("5. 测试总结")
print("=" * 50)
print(f"  设备:          {device}")
print(f"  模型大小:      {MODEL_SIZE}")
print(f"  转录耗时:      {transcribe_time:.1f}s")
print(f"  转录段落数:    {len(result['segments'])}")
print(f"  检测语言:      {result.get('language', 'N/A')}")
print(f"  模型加载时间:  {time.time() - t_start:.0f}s（含下载）")
print()
print("WhisperX 集成测试完成!")
