"""生成测试用音频文件 - 用于测试发音评测、对话、角色扮演、语法纠错等功能"""

import os
import wave
import struct
import math
import subprocess

# 输出目录
OUTPUT_DIR = "test_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SAMPLE_RATE = 16000  # 16kHz
DURATION = 3.0       # 3秒
AMPLITUDE = 16000    # 16-bit PCM 振幅


def generate_wav_sine(filename: str, freq: float = 440.0, duration: float = DURATION):
    """生成正弦波 WAV 文件 — 模拟浊音"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = []
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            # 频率微变模拟语调
            f = freq + 10 * math.sin(2 * math.pi * 0.5 * t)
            value = int(AMPLITUDE * math.sin(2 * math.pi * f * t))
            # 衰减包络
            env = max(0, 1 - t / duration) * (1 + 0.3 * math.sin(2 * math.pi * 3 * t))
            value = int(value * env)
            frames.append(struct.pack("<h", max(-32767, min(32767, value))))
        wf.writeframes(b"".join(frames))
    print(f"生成: {filepath} ({duration:.1f}s, {freq}Hz sine)")


def generate_wav_complex(filename: str, duration: float = DURATION):
    """生成复合波形 WAV 文件 — 更接近真实语音（多谐波 + 噪声）"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = []
        # 共振峰频率（模拟元音）
        formants = [500, 1500, 2500, 3500]
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            value = 0
            for j, fmt in enumerate(formants):
                amp = AMPLITUDE / (j + 1) / 3
                value += amp * math.sin(2 * math.pi * fmt * t)
                # 轻微频率调制
                value += amp * 0.3 * math.sin(2 * math.pi * (fmt + 50) * t)
            # 包络
            env = max(0, 1 - t / duration)
            value = int(value * env * 0.6)
            frames.append(struct.pack("<h", max(-32767, min(32767, value))))
        wf.writeframes(b"".join(frames))
    print(f"生成: {filepath} ({duration:.1f}s, formant-rich)")


def generate_wav_speech_like(filename: str, text: str = "hello world", duration: float = DURATION):
    """生成模拟语音波形 — 带音节包络的复合波"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    # 模拟音节节奏
    words = text.split()
    syllables_per_word = [max(1, len(w) // 2) for w in words]
    total_syllables = sum(syllables_per_word)
    syllable_dur = duration / total_syllables if total_syllables > 0 else duration

    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = []
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            # 哪个音节
            syllable_idx = min(int(t / syllable_dur), total_syllables - 1)
            syl_start = syllable_idx * syllable_dur
            syl_end = syl_start + syllable_dur
            syl_progress = (t - syl_start) / syllable_dur if syllable_dur > 0 else 0

            # 音节包络（起音快，衰减慢）
            syl_env = min(1.0, syl_progress * 3) * max(0, 1 - syl_progress * 0.5)

            # 基频随音节变化
            base_freq = 120 + syllable_idx * 15  # 音高渐变
            value = 0
            for h in range(1, 6):  # 5次谐波
                amp = AMPLITUDE / h / 4
                value += amp * math.sin(2 * math.pi * base_freq * h * t)
            value = int(value * syl_env * 0.8)
            frames.append(struct.pack("<h", max(-32767, min(32767, value))))
        wf.writeframes(b"".join(frames))
    print(f"生成: {filepath} ({duration:.1f}s, speech-like, text='{text}')")


def generate_silence(filename: str, duration: float = 1.0):
    """生成静音 WAV 文件 — 用于测试边界情况"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * n_samples)
    print(f"生成: {filepath} ({duration:.1f}s, silence)")


def generate_short_phrase(filename: str, duration: float = 1.5):
    """生成短语长度音频 — 用于测试发音评测短句"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = []
        base_freq = 150
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            # 模拟两音节短语
            if t < duration * 0.55:
                freq = base_freq  # 第一个音节
            else:
                freq = base_freq - 20  # 降调收尾
            value = 0
            for h in range(1, 4):
                value += (AMPLITUDE / h / 3) * math.sin(2 * math.pi * freq * h * t)
            env = math.sin(math.pi * t / duration)  # 平滑包络
            value = int(value * env * 0.7)
            frames.append(struct.pack("<h", max(-32767, min(32767, value))))
        wf.writeframes(b"".join(frames))
    print(f"生成: {filepath} ({duration:.1f}s, short-phrase)")


def generate_white_noise(filename: str, duration: float = 2.0):
    """生成白噪声 WAV — 测试噪声环境下 ASR 鲁棒性"""
    import random
    random.seed(42)
    filepath = os.path.join(OUTPUT_DIR, filename)
    n_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = []
        for _ in range(n_samples):
            value = int(random.gauss(0, AMPLITUDE * 0.15))
            frames.append(struct.pack("<h", max(-32767, min(32767, value))))
        wf.writeframes(b"".join(frames))
    print(f"生成: {filepath} ({duration:.1f}s, white-noise)")


if __name__ == "__main__":
    print("=" * 55)
    print("  Lingolab-ai 测试音频生成器")
    print("=" * 55)
    print(f"  输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  采样率: {SAMPLE_RATE} Hz, 16-bit mono WAV")
    print()

    # 1. 基础测试音频 - 不同长度
    generate_wav_sine("test_1s_440hz.wav", freq=440, duration=1.0)
    generate_wav_sine("test_2s_220hz.wav", freq=220, duration=2.0)
    generate_wav_sine("test_5s_330hz.wav", freq=330, duration=5.0)

    # 2. 模拟语音波形
    generate_wav_complex("test_complex_3s.wav", duration=3.0)

    # 3. 语音类波形（不同文本对应）
    phrases = [
        ("hello_how_are_you.wav", "hello how are you", 2.5),
        ("the_weather_is_nice.wav", "the weather is nice", 2.0),
        ("i_like_learning_english.wav", "i like learning english", 2.8),
        ("good_morning.wav", "good morning", 1.5),
        ("thank_you_very_much.wav", "thank you very much", 2.0),
    ]
    for fn, text, dur in phrases:
        generate_wav_speech_like(fn, text, dur)

    # 4. 短句（发音评测用）
    generate_short_phrase("short_phrase_1.wav", duration=1.5)
    generate_short_phrase("short_phrase_2.wav", duration=2.0)

    # 5. 边界情况
    generate_silence("silence_1s.wav", duration=1.0)
    generate_silence("silence_0.5s.wav", duration=0.5)
    generate_white_noise("white_noise_2s.wav", duration=2.0)

    # 6. 使用 ffmpeg 生成真实语音模拟（带音高变化的扫频信号）
    try:
        sweep_path = os.path.join(OUTPUT_DIR, "sweep_80_1000hz_3s.wav")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"sine=frequency=80:duration=3",
            "-af", "volume=-15dB",
            "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-sample_fmt", "s16",
            sweep_path,
        ], check=True, capture_output=True)
        print(f"生成: {sweep_path} (3.0s, ffmpeg sweep)")
    except Exception as e:
        print(f"跳过 ffmpeg sweep 生成: {e}")

    # 生成 MP3 测试文件（使用 ffmpeg 转换一个 wav）
    try:
        wav_path = os.path.join(OUTPUT_DIR, "test_2s_220hz.wav")
        mp3_path = os.path.join(OUTPUT_DIR, "test_2s_220hz.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-b:a", "64k",
            mp3_path,
        ], check=True, capture_output=True)
        print(f"生成: {mp3_path} (MP3 格式)")

        # 生成 webm 格式（浏览器录音常用格式）
        webm_path = os.path.join(OUTPUT_DIR, "test_2s_220hz.webm")
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-c:a", "libopus", "-b:a", "48k",
            webm_path,
        ], check=True, capture_output=True)
        print(f"生成: {webm_path} (WebM Opus 格式)")
    except Exception as e:
        print(f"跳过 MP3/WebM 生成: {e}")

    print()
    print("=" * 55)
    print(f"  完成！共生成测试音频文件到: {OUTPUT_DIR}/")
    print("=" * 55)
    print()
    print("使用方法:")
    print("  1. 发音评测测试:")
    print(f"     curl -X POST http://localhost:8000/api/pronunciation/evaluate \\")
    print(f"       -F \"audio=@{OUTPUT_DIR}/test_2s_220hz.wav\" \\")
    print(f"       -F \"text=hello\" -F \"mode=sentence\"")
    print()
    print("  2. 对话测试 (先创建会话):")
    print(f"     # 查看 /api/conversation/ 端点")
    print()
    print("  3. 角色扮演测试:")
    print(f"     # 查看 /api/roleplay/ 端点")
    print()
    print("  4. 语法纠错测试:")
    print(f"     # 查看 /api/grammar/ 端点")
