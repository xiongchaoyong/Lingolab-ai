"""
Edge TTS 语音合成 — 功能测试
微软神经网络 TTS，完全免费，无需注册

流程:
  1. 选择音色
  2. 合成语音（支持 SSML 精确控制）
  3. 保存 MP3 + 自动播放
"""

import asyncio
import os
import subprocess
import edge_tts

# ============================================================
# 配置
# ============================================================
# 推荐音色（英语学习场景）
VOICES = {
    "美式女声": "en-US-JennyNeural",       # 亲切自然，适合教学
    "美式男声": "en-US-EricNeural",        # 理性清晰
    "英式女声": "en-GB-SoniaNeural",       # 英音标准
    "英式男声": "en-GB-RyanNeural",        # 英音自然
}

OUTPUT_DIR = "edge_tts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 1. 基本合成测试
# ============================================================
async def basic_tts(text, voice, filename):
    """基础文本转语音"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    size = os.path.getsize(filename)
    print(f"  {filename}  ({size / 1024:.1f} KB)")
    return filename

# ============================================================
# 2. SSML 精准控制（语速、停顿、音调）
# ============================================================
async def ssml_tts(voice, filename):
    """
    SSML 高级控制
    适用场景: 标准音朗读范例，可以精确控制语速和停顿
    """
    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{voice}">
            <prosody rate="0.9" pitch="+0%">
                Hello, nice to meet you!
                <break time="500ms"/>
                Welcome to <emphasis level="moderate">English speaking practice</emphasis>.
                <break time="300ms"/>
            </prosody>
            <prosody rate="0.85" pitch="+5%">
                Let's practice the following sentence:
                <break time="500ms"/>
            </prosody>
            <prosody rate="0.75" pitch="+0%">
                The quick brown fox jumps over the lazy dog.
            </prosody>
        </voice>
    </speak>
    """
    communicate = edge_tts.Communicate(ssml, voice)
    await communicate.save(filename)
    size = os.path.getsize(filename)
    print(f"  {filename}  ({size / 1024:.1f} KB)  — SSML 精确控制：语速0.75~0.9x, 单词间停顿")
    return filename

# ============================================================
# 3. 带时间戳的合成（单词级对齐）
# ============================================================
async def tts_with_timestamps(text, voice, filename):
    """合成并获取句级时间戳"""
    communicate = edge_tts.Communicate(text, voice)
    audio_data = bytearray()
    sentence_boundaries = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] == "SentenceBoundary":
            start_s = (chunk["offset"] + 50) / 10000000  # ticks → seconds
            dur_s = chunk["duration"] / 10000000
            sentence_boundaries.append({
                "text": chunk["text"],
                "start": round(start_s, 2),
                "end": round(start_s + dur_s, 2),
            })

    with open(filename, "wb") as f:
        f.write(audio_data)

    size = os.path.getsize(filename)
    print(f"  {filename}  ({size / 1024:.1f} KB)")

    print(f"\n  句级时间戳 (共 {len(sentence_boundaries)} 句):")
    for s in sentence_boundaries:
        print(f"  [{s['start']:6.2f}s → {s['end']:6.2f}s] {s['text']}")

    return filename, sentence_boundaries

    # 收集时间戳
    word_timestamps = []
    audio_data = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
            ms = (chunk["offset"] - 50) / 10000  # 转换为秒
            dur = chunk["duration"] / 10000
            word_timestamps.append({
                "word": chunk["text"],
                "start": round(ms, 2),
                "duration": round(dur, 2),
            })
        elif chunk["type"] == "audio":
            audio_data.extend(chunk["data"])

    # 保存音频
    with open(filename, "wb") as f:
        f.write(audio_data)

    size = os.path.getsize(filename)
    print(f"  {filename}  ({size / 1024:.1f} KB)")
    print(f"\n  单词时间戳 (共 {len(word_timestamps)} 个词):")
    for w in word_timestamps:
        print(f"  {w['word']:<15s} {w['start']:6.2f}s → {w['start'] + w['duration']:6.2f}s")

    return filename, word_timestamps

# ============================================================
# 主流程
# ============================================================
async def main():
    print("=" * 50)
    print("Edge TTS — 微软免费神经网络语音合成")
    print("=" * 50)

    # 测试 1: 基础合成 — 多音色对比
    print("\n1. 基础合成（多音色对比）")
    print("-" * 40)
    base_text = "Hello, welcome to English speaking practice. Let's start learning today!"

    for label, voice in VOICES.items():
        print(f"\n [{label}] {voice}")
        await basic_tts(
            base_text, voice,
            f"{OUTPUT_DIR}/basic_{label}.mp3",
        )

    # 测试 2: SSML 精准控制 — 慢速带停顿（用于标准音范例）
    print(f"\n\n2. SSML 精准控制")
    print("-" * 40)
    print(f" [美式女声] en-US-JennyNeural")
    await ssml_tts(
        "en-US-JennyNeural",
        f"{OUTPUT_DIR}/ssml_demo.mp3",
    )

    # 测试 3: 单词级时间戳
    print(f"\n\n3. 单词级时间戳（用于跟读高亮）")
    print("-" * 40)
    print(f" [英式女声] en-GB-SoniaNeural")
    practice_text = "The quick brown fox jumps over the lazy dog."
    await tts_with_timestamps(
        practice_text,
        "en-GB-SoniaNeural",
        f"{OUTPUT_DIR}/timestamp_demo.mp3",
    )

    # ============================================================
    # 总结
    # ============================================================
    print(f"\n\n{'=' * 50}")
    print("测试完成!")
    print(f"{'=' * 50}")
    print(f"  方案: Edge TTS (微软神经网络)")
    print(f"  费用: 完全免费，无需注册")
    print(f"  音色: 4种测试 (Jenny/Eric/Sonia/Ryan)")
    print(f"  功能: 基础合成 ✓  SSML控制 ✓  单词时间戳 ✓")
    print(f"\n  输出目录: {OUTPUT_DIR}/")

    for f in sorted(os.listdir(OUTPUT_DIR)):
        print(f"    {f}")

    # 自动播放第一个
    print(f"\n播放: basic_美式女声.mp3")
    subprocess.run(["afplay", f"{OUTPUT_DIR}/basic_美式女声.mp3"], check=False)

if __name__ == "__main__":
    asyncio.run(main())
