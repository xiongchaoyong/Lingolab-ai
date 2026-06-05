"""
wav2vec2 发音评测 — 完整流程测试
基于 GOP (Goodness of Pronunciation) 算法

流程:
  1. 用 macOS say 生成标准音（参考）
  2. 用 say 生成「错误发音」版本（模拟学习者）
  3. wav2vec2 提取特征 + CTC 强制对齐
  4. 比较音素级后验概率 → 打分
"""

import os
import time
import subprocess
import torch
import torchaudio
import numpy as np

# ============================================================
# 0. 环境配置
# ============================================================
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"设备: {DEVICE}")

# ============================================================
# 1. 生成测试音频（模拟标准音 vs 学习者发音）
# ============================================================
TEST_SENTENCE = "The cat sat on the mat."

def generate_audio(text, filename, voice="Samantha"):
    """用 macOS say 生成音频"""
    if not os.path.exists(filename):
        cmd = ["say", text, "-v", voice, "-o", filename.replace(".wav", ".aiff")]
        subprocess.run(cmd, check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-i", filename.replace(".wav", ".aiff"),
             "-ac", "1", "-ar", "16000", filename],
            check=True, capture_output=True,
        )
        os.remove(filename.replace(".wav", ".aiff"))

print("\n生成测试音频...")
generate_audio(TEST_SENTENCE, "test_native.wav")
generate_audio(TEST_SENTENCE, "test_native.wav")  # 作为「学习者」版本（实际用真实录音时替换）
print("测试音频就绪")

# ============================================================
# 2. 加载 wav2vec2 模型
# ============================================================
print("\n加载 wav2vec2 模型...")
bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
model = bundle.get_model().to(DEVICE)
labels = bundle.get_labels()  # [<s>, A, B, C, ..., Z, ', |, </s>]
print(f"模型参数: {sum(p.numel() for p in model.parameters()) / 1e6:.0f}M")
print(f"输出类别: {len(labels)}  (字符级 CTC: A-Z, ', |, 空格)")

# ============================================================
# 3. 音频 → wav2vec2 特征
# ============================================================
def extract_features(audio_path):
    """加载音频,提取 wav2vec2 特征"""
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
    waveform = waveform.to(DEVICE)

    with torch.no_grad():
        emission, _ = model(waveform)
    # emission: (1, time_frames, num_labels) — CTC softmax 后验概率
    emission = torch.log_softmax(emission, dim=-1)
    return emission.cpu(), waveform

emission, waveform = extract_features("test_native.wav")
print(f"\n音频长度: {waveform.shape[1] / 16000:.1f}s")
print(f"特征帧数: {emission.shape[1]}, 每帧 {(waveform.shape[1] / emission.shape[1] / 16000 * 1000):.0f}ms")

# ============================================================
# 4. 文本 → 音素（G2P）
# ============================================================
print("\n=== 音素转换 (G2P) ===")

from g2p_en import G2p
g2p = G2p()

# 转换为音素序列
text_clean = TEST_SENTENCE.lower().strip()
phonemes = g2p(text_clean)
print(f"文本:   {text_clean}")
print(f"音素:   {' '.join(phonemes)}")

# ============================================================
# 5. CTC 强制对齐 — 核心算法
# ============================================================
print("\n=== CTC 强制对齐 ===")

def ctc_forced_alignment(emission, text, labels):
    """
    CTC 强制对齐：给定音频的后验概率和期望文本，
    找出文本中每个字符对应的音频帧范围。

    算法: 在 CTC 标签序列上做 Viterbi 对齐
    """
    # 构建 CTC token 序列（允许 blank 插入）
    # labels[0] = <s> (blank)，实际字母从 index 1 开始
    char_to_index = {c: i for i, c in enumerate(labels)}

    target = []
    for ch in text.upper():
        if ch in char_to_index:
            target.append(char_to_index[ch])
        elif ch == ' ':
            target.append(char_to_index['|'])  # 空格用 | 表示

    # Viterbi 对齐 — 在 CTC 格上找最优路径
    T = emission.shape[1]  # 帧数
    S = len(target)        # 目标序列长度

    # CTC 扩展：每个 token 间可以插入 blank
    # 扩展序列: blank, t0, blank, t1, blank, ...
    extended = [0]  # labels[0] = blank
    for t in target:
        extended.append(t)
        extended.append(0)  # blank

    # 对数概率
    log_prob = emission[0]  # (T, num_labels)

    # Viterbi DP
    dp = torch.full((T, len(extended)), float('-inf'))
    backtrack = torch.zeros((T, len(extended)), dtype=torch.long)

    # 初始化: 第 0 帧可以是 blank 或第一个 token
    dp[0, 0] = log_prob[0, 0]  # blank
    dp[0, 1] = log_prob[0, extended[1]]  # first char

    for t in range(1, T):
        for s in range(len(extended)):
            if dp[t-1, s] == float('-inf'):
                continue

            # 路径 1: 停留在同一点 (blank → blank, char → char)
            prob = dp[t-1, s] + log_prob[t, extended[s]]
            if prob > dp[t, s]:
                dp[t, s] = prob
                backtrack[t, s] = s

            # 路径 2: 前进一个 (blank → char，可跳过)
            if s + 1 < len(extended):
                prob = dp[t-1, s] + log_prob[t, extended[s+1]]
                if prob > dp[t, s+1]:
                    dp[t, s+1] = prob
                    backtrack[t, s+1] = s

            # 路径 3: 前进两个 (char → blank → next_char，跳过 blank)
            if s + 2 < len(extended):
                prob = dp[t-1, s] + log_prob[t, extended[s+2]]
                if prob > dp[t, s+2]:
                    dp[t, s+2] = prob
                    backtrack[t, s+2] = s

    # 回溯 — 从最后一帧的最佳结束点开始
    # 结束点: 最后一个字符 或 blank
    end_idx = len(extended) - 1
    if dp[T-1, end_idx-1] > dp[T-1, end_idx]:
        end_idx = end_idx - 1

    best_path = []
    idx = end_idx
    for t in range(T-1, -1, -1):
        best_path.append(idx)
        idx = backtrack[t, idx].item()
    best_path.reverse()

    # 将路径映射回目标序列
    alignments = []  # [(char, start_frame, end_frame)]
    current_char_idx = None
    current_start = 0

    for t, s in enumerate(best_path):
        # 判断 s 对应的是原序列中的哪个位置
        char_pos = None
        if s > 0:
            # 在 extended 序列中奇数位置是真实字符
            orig_idx = (s - 1) // 2
            if s % 2 == 1 and orig_idx < len(target):  # 是字符不是 blank
                char_pos = orig_idx

        if char_pos != current_char_idx:
            if current_char_idx is not None and current_start < t:
                alignments.append((current_char_idx, current_start, t))
            current_char_idx = char_pos
            current_start = t

    if current_char_idx is not None:
        alignments.append((current_char_idx, current_start, T))

    return target, alignments, log_prob, best_path

target_indices, alignments, log_prob, best_path = ctc_forced_alignment(emission, text_clean, labels)

# 打印对齐结果
print("帧级对齐结果:")
for char_idx, start_f, end_f in alignments:
    ch = labels[target_indices[char_idx]]
    dur_ms = (end_f - start_f) * (waveform.shape[1] / emission.shape[1] / 16000 * 1000)
    # 该字符在区间内的平均对数概率
    seg_prob = log_prob[start_f:end_f, target_indices[char_idx]].mean().exp().item()
    print(f"  {ch}  [{start_f:3d}→{end_f:3d}]  {dur_ms:5.0f}ms  置信度: {seg_prob:.2f}")

# ============================================================
# 6. 发音评分（简化版 GOP）
# ============================================================
print("\n=== 发音评分 ===")

def compute_gop_scores(target_indices, alignments, log_prob, labels):
    """
    计算每个音素的 GOP (Goodness of Pronunciation) 分数

    GOP = log(p(phoneme|acoustic)) / duration
    高分 = 发音接近母语者
    """
    scores = []
    for char_idx, start_f, end_f in alignments:
        ch = labels[target_indices[char_idx]]
        dur = end_f - start_f
        if dur == 0:
            continue
        # 平均对数后验概率
        avg_log_prob = log_prob[start_f:end_f, target_indices[char_idx]].mean()
        # 归一化到 0~100
        gop_score = float(avg_log_prob.exp() * 100)
        scores.append({
            "char": ch,
            "duration_ms": round(dur * 20, 1),  # 近似: 每帧 ~20ms
            "score": round(gop_score, 1),
            "level": "优秀" if gop_score > 80 else "良好" if gop_score > 60 else "一般" if gop_score > 40 else "需练习"
        })
    return scores

scores = compute_gop_scores(target_indices, alignments, log_prob, labels)

print(f"{'字符':<8} {'时长':<10} {'得分':<8} {'评级'}")
print("-" * 40)
total_score = 0
for s in scores:
    print(f"  {s['char']:<8} {s['duration_ms']:<5.0f}ms   {s['score']:<5.1f}     {s['level']}")
    total_score += s['score']

avg_score = total_score / len(scores) if scores else 0
print("-" * 40)
print(f"  综合得分: {avg_score:.0f}/100")

# ============================================================
# 7. 总结
# ============================================================
print("\n" + "=" * 50)
print("发音评测流程总结")
print("=" * 50)
print(f"  模型: wav2vec2 ASR Base (960h fine-tuned)")
print(f"  算法: GOP (Goodness of Pronunciation)")
print(f"  设备: {DEVICE}")
print(f"  测试文本: {TEST_SENTENCE}")
print(f"  综合得分: {avg_score:.0f}/100")
print()
print("架构: 音频 → wav2vec2 → CTC强制对齐 → 逐帧后验概率 → GOP分数")
