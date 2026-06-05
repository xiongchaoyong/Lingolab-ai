"""发音评测服务 — 基于 wav2vec2 + CTC 强制对齐 + GOP 算法"""

import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional

import torch
import torchaudio
import numpy as np
import librosa
import whisperx

logger = logging.getLogger(__name__)

# 推理线程池（避免阻塞事件循环）
_executor = ThreadPoolExecutor(max_workers=2)

# 全局单例
_service_instance = None

# 常见音素的纠错建议映射
PHONEME_TIPS: Dict[str, str] = {
    "TH": "舌尖轻触上齿，气流从齿缝挤出，声带振动",
    "DH": "舌尖轻触上齿，气流从齿缝挤出，声带不振动",
    "R": "舌尖卷起靠近上颚但不要接触，嘴唇微微收圆",
    "L": "舌尖抵上齿龈，气流从舌侧溢出",
    "W": "双唇收圆送出气流，声带振动",
    "V": "上齿轻咬下唇，气流挤出时声带振动",
    "F": "上齿轻咬下唇，气流挤出时声带不振动",
    "AE": "舌尖抵下齿，舌前部向硬腭抬起，口型张大",
    "EH": "舌尖抵下齿，舌前部稍抬起，口型半开",
    "IH": "舌尖抵下齿，舌前部抬高，口型微开",
    "AH": "舌尖放松，口腔中部自然打开",
    "UH": "双唇收圆微突，舌后部抬高",
    "AO": "双唇收圆，舌后部抬高，口型较大",
    "AA": "口张大，舌身放平，舌尖离开下齿",
    "IY": "舌前部抬高贴近硬腭，嘴角向两边拉开",
    "UW": "双唇收圆突出，舌后部向软腭抬高",
    "S": "舌尖靠近上齿龈但不接触，气流从齿缝挤出",
    "Z": "舌尖靠近上齿龈但不接触，气流挤出时声带振动",
    "SH": "舌尖靠近硬腭前端，双唇微突，气流挤出",
    "CH": "舌尖抵上齿龈堵住气流，然后释放产生摩擦",
    "JH": "与 CH 相同但声带振动",
    "NG": "舌后部顶住软腭，气流从鼻腔出来，声带振动",
    "P": "双唇紧闭憋气，然后突然释放",
    "T": "舌尖顶上齿龈憋气，然后突然释放",
    "K": "舌后部顶软腭憋气，然后突然释放",
    "B": "与 P 相同但声带振动",
    "D": "与 T 相同但声带振动",
    "G": "与 K 相同但声带振动",
    "M": "双唇紧闭，气流从鼻腔出来",
    "N": "舌尖顶上齿龈，气流从鼻腔出来",
    "HH": "口腔自然张开，气流从声门呼出",
}


class PronunciationService:
    """wav2vec2 发音评测服务"""

    def __init__(self, device: str = "auto"):
        if device == "auto":
            self.device = torch.device(
                "mps" if torch.backends.mps.is_available() else "cpu"
            )
        else:
            self.device = torch.device(device)

        logger.info(f"发音评测设备: {self.device}")
        self.model = None
        self.labels = None
        self.g2p = None
        self.whisperx_model = None
        self.whisperx_align = None
        self._loaded = False

    def load(self):
        """加载 wav2vec2 模型 + G2P 实例"""
        if self._loaded:
            return

        logger.info("加载 wav2vec2 模型...")
        bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        self.model = bundle.get_model().to(self.device)
        self.labels = bundle.get_labels()
        model_params = sum(p.numel() for p in self.model.parameters()) / 1e6
        logger.info(f"wav2vec2 模型加载完成: {model_params:.0f}M 参数, {len(self.labels)} 输出类别")

        logger.info("加载 G2P 音素转换器...")
        from g2p_en import G2p
        self.g2p = G2p()
        logger.info("G2P 加载完成")

        # 加载 WhisperX（用于连读分析 + 后续流利度评估）
        logger.info("加载 WhisperX small 模型...")
        device_str = "cpu"
        if self.device.type == "mps":
            device_str = "cpu"  # WhisperX 在 MPS 上不稳定，使用 CPU int8
        self.whisperx_model = whisperx.load_model(
            "small", device_str, compute_type="int8"
        )
        self.whisperx_align, self.whisperx_metadata = whisperx.load_align_model(
            language_code="en", device=device_str
        )
        logger.info("WhisperX 加载完成")
        self._loaded = True

    def _extract_features(self, audio_path: str):
        """加载音频，通过 wav2vec2 提取对数后验概率"""
        waveform, sr = torchaudio.load(audio_path)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
        waveform = waveform.to(self.device)

        with torch.no_grad():
            emission, _ = self.model(waveform)
        emission = torch.log_softmax(emission, dim=-1)
        return emission.cpu(), waveform

    def _text_to_phonemes(self, text: str) -> List[str]:
        """文本 → 音素序列（G2P）"""
        text_clean = text.lower().strip()
        return self.g2p(text_clean)

    def _ctc_forced_alignment(
        self,
        emission: torch.Tensor,
        text: str,
    ) -> Tuple[List[int], List[Tuple[int, int, int]], torch.Tensor, List[int]]:
        """CTC 强制对齐：在音频后验概率上做 Viterbi 对齐"""
        char_to_index = {c: i for i, c in enumerate(self.labels)}

        target = []
        for ch in text.upper():
            if ch in char_to_index:
                target.append(char_to_index[ch])
            elif ch == " ":
                target.append(char_to_index.get("|", char_to_index.get(" ")))
            elif ch == "'":
                target.append(char_to_index.get("'", target[-1] if target else 0))

        if not target:
            return [], [], emission[0], []

        T = emission.shape[1]
        S = len(target)

        # CTC 扩展序列: blank, t0, blank, t1, blank, ...
        extended = [0]  # labels[0] = blank
        for t in target:
            extended.append(t)
            extended.append(0)

        log_prob = emission[0]

        # Viterbi DP
        dp = torch.full((T, len(extended)), float("-inf"))
        backtrack = torch.zeros((T, len(extended)), dtype=torch.long)

        dp[0, 0] = log_prob[0, 0]
        dp[0, 1] = log_prob[0, extended[1]]

        for t in range(1, T):
            for s in range(len(extended)):
                if dp[t - 1, s] == float("-inf"):
                    continue

                # 停留
                prob = dp[t - 1, s] + log_prob[t, extended[s]]
                if prob > dp[t, s]:
                    dp[t, s] = prob
                    backtrack[t, s] = s

                # 前进 1
                if s + 1 < len(extended):
                    prob = dp[t - 1, s] + log_prob[t, extended[s + 1]]
                    if prob > dp[t, s + 1]:
                        dp[t, s + 1] = prob
                        backtrack[t, s + 1] = s

                # 前进 2（跳过 blank）
                if s + 2 < len(extended):
                    prob = dp[t - 1, s] + log_prob[t, extended[s + 2]]
                    if prob > dp[t, s + 2]:
                        dp[t, s + 2] = prob
                        backtrack[t, s + 2] = s

        # 回溯
        end_idx = len(extended) - 1
        if dp[T - 1, end_idx - 1] > dp[T - 1, end_idx]:
            end_idx = end_idx - 1

        best_path = []
        idx = end_idx
        for t in range(T - 1, -1, -1):
            best_path.append(idx)
            idx = backtrack[t, idx].item()
        best_path.reverse()

        # 映射回目标序列
        alignments = []
        current_char_idx = None
        current_start = 0

        for t, s in enumerate(best_path):
            char_pos = None
            if s > 0 and s % 2 == 1:
                orig_idx = (s - 1) // 2
                if orig_idx < len(target):
                    char_pos = orig_idx

            if char_pos != current_char_idx:
                if current_char_idx is not None and current_start < t:
                    alignments.append((current_char_idx, current_start, t))
                current_char_idx = char_pos
                current_start = t

        if current_char_idx is not None:
            alignments.append((current_char_idx, current_start, T))

        return target, alignments, log_prob, best_path

    def _compute_gop_scores(
        self,
        target_indices: List[int],
        alignments: List[Tuple[int, int, int]],
        log_prob: torch.Tensor,
    ) -> Tuple[List[Dict], float]:
        """计算 GOP 分数并生成音素级评分报告"""
        scores = []
        total_score = 0.0

        for char_idx, start_f, end_f in alignments:
            ch = self.labels[target_indices[char_idx]]
            # 过滤 CTC 特殊 token（空白符、静音等）
            if ch in ("|", "<s>", "</s>", " "):
                continue
            dur = end_f - start_f
            if dur == 0:
                continue

            avg_log_prob = float(log_prob[start_f:end_f, target_indices[char_idx]].mean())
            gop_score = float(np.exp(avg_log_prob) * 100)

            # 评分等级
            if gop_score > 80:
                level = "优秀"
            elif gop_score > 60:
                level = "良好"
            elif gop_score > 40:
                level = "一般"
            else:
                level = "需练习"

            scores.append({
                "char": ch,
                "score": round(gop_score, 1),
                "duration_ms": round((end_f - start_f) * 20, 1),
                "level": level,
            })
            total_score += gop_score

        avg_score = round(total_score / len(scores), 1) if scores else 0.0
        return scores, avg_score

    def _generate_error_tips(self, char_scores: List[Dict], text: str) -> List[Dict]:
        """根据低分音素生成纠错建议"""
        errors = []
        seen_phonemes = set()

        for item in char_scores:
            if item["score"] < 55 and item["char"] not in seen_phonemes:
                ch = item["char"]
                seen_phonemes.add(ch)
                actual_mark = f"/{ch.lower()}/"
                tip = PHONEME_TIPS.get(ch, "注意该音素的标准发音位置")

                errors.append({
                    "phoneme": ch,
                    "actual": actual_mark,
                    "score": item["score"],
                    "tip": tip,
                })

        return errors[:5]  # 最多 5 个错误音素

    def _analyze_stress(
        self,
        audio_path: str,
        alignments: List[Tuple[int, int, int]],
        target_indices: List[int],
        phonemes: List[str],
    ) -> Tuple[float, str, Dict]:
        """
        重音位置分析 — 基于音频能量包络 + 时长

        返回: (score, detail, viz_data)
        viz_data: { chars, energies, durations, is_stressed, energy_cv, dur_cv }
        """
        viz_data = {"chars": [], "energies": [], "durations": [], "is_stressed": []}

        try:
            y, sr = librosa.load(audio_path, sr=16000)
            hop_length = 320
            rms = librosa.feature.rms(y=y, hop_length=hop_length, frame_length=640)[0]

            char_data = []
            for char_idx, start_f, end_f in alignments:
                ch = self.labels[target_indices[char_idx]]
                if ch in ("|", "<s>", "</s>", " "):
                    continue
                dur_frames = end_f - start_f
                if dur_frames <= 0:
                    continue
                s, e = max(0, start_f), min(len(rms), end_f)
                seg_energy = float(rms[s:e].mean()) if s < e else 0.0
                char_data.append({
                    "char": ch,
                    "energy": seg_energy,
                    "duration_frames": dur_frames,
                })

            if not char_data or len(char_data) < 2:
                return 50.0, "数据不足，无法分析重音", viz_data

            energies = np.array([d["energy"] for d in char_data])
            durations = np.array([d["duration_frames"] for d in char_data])
            energy_mean = float(energies.mean())

            if energy_mean < 1e-8:
                return 50.0, "音频能量过低，无法分析重音", viz_data

            # 归一化能量 0~1
            energy_min, energy_max = float(energies.min()), float(energies.max())
            if energy_max > energy_min:
                energies_norm = (energies - energy_min) / (energy_max - energy_min)
            else:
                energies_norm = np.ones_like(energies) * 0.5

            energy_cv = float(energies.std() / energy_mean)
            dur_cv = float(durations.std() / durations.mean()) if durations.mean() > 0 else 0

            # 标注重音字符 (能量 > 1.3x 均值)
            stress_threshold = energy_mean * 1.3
            is_stressed = [float(d["energy"]) > stress_threshold for d in char_data]

            # 填充可视化数据
            viz_data = {
                "chars": [d["char"] for d in char_data],
                "energies": [round(float(e), 3) for e in energies_norm],
                "durations": [int(d["duration_frames"]) for d in char_data],
                "is_stressed": [bool(s) for s in is_stressed],
                "energy_cv": round(energy_cv, 3),
                "dur_cv": round(dur_cv, 3),
            }

            # 评分
            if energy_cv < 0.05:
                stress_score = 30.0 + energy_cv * 200
                detail = "能量过于平坦，缺乏重音变化，建议加强实词重读"
            elif energy_cv < 0.15:
                stress_score = 50.0 + (energy_cv - 0.05) * 300
                detail = "有轻微能量变化，重音区分不够明显"
            elif energy_cv < 0.4:
                stress_score = 70.0 + (energy_cv - 0.15) * 80
                detail = "能量起伏自然，重音分布合理"
            elif energy_cv < 0.8:
                stress_score = 90.0 - (energy_cv - 0.4) * 50
                detail = "重音变化明显，注意部分音节可能过重"
            else:
                stress_score = 60.0
                detail = "能量起伏过大，发音不稳定"

            if dur_cv > 0.3 and energy_cv > 0.15:
                stress_score = min(stress_score + 5, 100)
                detail += "；时长分布有节奏感"
            elif dur_cv < 0.05:
                stress_score = max(stress_score - 10, 0)
                detail += "；时长过于均匀缺乏重音变化"

            stress_score = round(min(max(stress_score, 0), 100))
            return stress_score, detail, viz_data

        except Exception as e:
            logger.warning(f"重音分析失败: {e}")
            return 50.0, "重音分析异常", viz_data

    def _analyze_intonation(
        self,
        audio_path: str,
        text: str,
    ) -> Tuple[float, str, Dict]:
        """
        语调曲线分析 — 基于 F0 基频提取 + 趋势拟合

        返回: (score, detail, viz_data)
        viz_data: { direction, range_st, f0_points, sentence_type, slope_st_per_sec }
        """
        viz_data = {
            "direction": "unknown",
            "range_st": 0.0,
            "f0_points": [],
            "sentence_type": "statement",
            "slope_st_per_sec": 0.0,
        }

        try:
            y, sr = librosa.load(audio_path, sr=16000)

            f0, voiced_flag, voiced_prob = librosa.pyin(
                y, fmin=50, fmax=500, sr=sr
            )
            if f0 is None or len(f0) < 5:
                return 50.0, "无法提取基频，请检查音频质量", viz_data

            voiced_f0 = f0[voiced_flag]
            if len(voiced_f0) < 5:
                return 50.0, "有效基频帧过少", viz_data

            t = np.arange(len(f0))
            valid_mask = ~np.isnan(f0)
            if valid_mask.sum() < 3:
                return 50.0, "有效基频数据不足", viz_data

            t_valid = t[valid_mask]
            f0_valid = f0[valid_mask]
            f0_log = np.log2(f0_valid)
            coeffs = np.polyfit(t_valid, f0_log, 1)
            slope_log2_per_frame = coeffs[0]
            frames_per_sec = sr / 512
            slope_semitones_per_sec = slope_log2_per_frame * 12 * frames_per_sec

            f0_range_semitones = float(12 * (np.log2(f0_valid.max()) - np.log2(f0_valid.min())))

            # 降采样 F0 点用于前端绘图（最多 50 个点）
            step = max(1, len(f0) // 50)
            sampled_f0 = []
            for i in range(0, len(f0), step):
                chunk = f0[i:i+step]
                valid_chunk = chunk[~np.isnan(chunk)]
                if len(valid_chunk) > 0:
                    sampled_f0.append({
                        "t": round(i / frames_per_sec, 2),  # 秒
                        "hz": round(float(valid_chunk.mean()), 1),
                    })

            # 判断方向
            if slope_semitones_per_sec > 0.8:
                direction = "↗ 上升"
            elif slope_semitones_per_sec > 0.2:
                direction = "↗ 微升"
            elif slope_semitones_per_sec > -0.2:
                direction = "→ 持平"
            elif slope_semitones_per_sec > -0.8:
                direction = "↘ 微降"
            else:
                direction = "↘ 下降"

            is_question = text.strip().endswith("?")
            is_exclamation = text.strip().endswith("!")
            if is_question:
                sentence_type = "question"
            elif is_exclamation:
                sentence_type = "exclamation"
            else:
                sentence_type = "statement"

            viz_data = {
                "direction": direction,
                "range_st": round(f0_range_semitones, 1),
                "f0_points": sampled_f0,
                "sentence_type": sentence_type,
                "slope_st_per_sec": round(slope_semitones_per_sec, 2),
            }

            # 评分
            if f0_range_semitones < 1.5:
                intonation_score = 30.0
                detail = "语调过于平坦，缺乏抑扬顿挫，建议增加语调起伏"
            elif is_question:
                if slope_semitones_per_sec > 0.5:
                    score = 85.0
                    detail = "疑问句语调上扬自然，符合预期"
                elif slope_semitones_per_sec > 0:
                    score = 70.0
                    detail = "疑问句有轻微升调，可更明显一些"
                elif slope_semitones_per_sec > -1.0:
                    score = 50.0
                    detail = "疑问句语调偏平或微降，建议句尾上扬"
                else:
                    score = 35.0
                    detail = "疑问句语调明显下降，应改为句尾上扬"
                if f0_range_semitones > 5:
                    score = min(score + 10, 100)
                    detail += "；音高变化丰富"
                intonation_score = score
            elif is_exclamation:
                if f0_range_semitones > 5:
                    intonation_score = 80.0
                    detail = "感叹句语调起伏明显，表达有力"
                else:
                    intonation_score = 55.0
                    detail = "感叹句语调变化可更夸张一些"
            else:
                if -2.0 <= slope_semitones_per_sec <= -0.3:
                    intonation_score = 85.0
                    detail = "陈述句语调自然下降，符合母语者习惯"
                elif -0.3 < slope_semitones_per_sec < 0.3:
                    intonation_score = 60.0
                    detail = "陈述句语调偏平，建议句尾自然降调"
                elif slope_semitones_per_sec < -4.0:
                    intonation_score = 55.0
                    detail = "语调下降过快，发音可能断断续续"
                elif slope_semitones_per_sec > 0.5:
                    intonation_score = 45.0
                    detail = "陈述句语调上扬，容易让听者以为你在提问"
                else:
                    intonation_score = 65.0
                    detail = "语调基本正常，可适当增加句尾下降感"
                if f0_range_semitones > 4:
                    intonation_score = min(intonation_score + 10, 100)
                    detail += "；音高变化丰富"

            intonation_score = round(min(max(intonation_score, 0), 100))
            return intonation_score, detail, viz_data

        except Exception as e:
            logger.warning(f"语调分析失败: {e}")
            return 50.0, "语调分析异常", viz_data

    # ARPABET 辅音/元音分类（用于判断连读条件）
    _CONSONANTS = set(
        "B CH D DH F G HH JH K L M N NG P R S SH T TH V W Y Z ZH".split()
    )
    _VOWELS = set(
        "AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW".split()
    )

    def _transcribe_whisperx(self, audio_path: str) -> List[Dict]:
        """使用 WhisperX 转录音频并返回词级时间戳"""
        try:
            result = self.whisperx_model.transcribe(audio_path, batch_size=1)
            aligned = whisperx.align(
                result["segments"],
                self.whisperx_align,
                self.whisperx_metadata,
                audio_path,
                device=self.whisperx_model.device,
            )
            words = []
            for seg in aligned.get("word_segments", aligned.get("segments", [])):
                if "words" in seg:
                    words.extend(seg["words"])
                elif "word" in seg:
                    words.append(seg)
            return words
        except Exception as e:
            logger.warning(f"WhisperX 转录失败: {e}")
            return []

    def _classify_phoneme(self, phoneme: str) -> str:
        """判断 ARPABET 音素是辅音还是元音（去除重音数字后缀如 AH0→AH）"""
        p = phoneme.rstrip("012")
        if p in self._CONSONANTS:
            return "consonant"
        if p in self._VOWELS:
            return "vowel"
        return "unknown"

    def _analyze_linking(
        self,
        audio_path: str,
        text: str,
    ) -> Tuple[float, str, Dict]:
        """
        连读表现分析 — 基于 WhisperX 词级时间戳 + G2P 辅元连读条件

        流程:
        1. WhisperX 转录 → 词级时间戳
        2. 对每对相邻词，G2P 判断是否存在辅音→元音连读条件
        3. 计算词间间隙 gap = word[i+1].start - word[i].end
        4. 按 gap 大小打分

        返回: (score, detail, viz_data)
        """
        viz_data = {
            "pairs": [],
            "linkable_count": 0,
            "linked_count": 0,
            "avg_gap_ms": 0.0,
        }

        # 获取词级时间戳
        words = self._transcribe_whisperx(audio_path)
        if not words or len(words) < 2:
            return 75.0, "词数不足，无法分析连读", viz_data

        # 过滤短词（噪声），保留有效词
        valid_words = []
        for w in words:
            word_text = w.get("word", "").strip()
            if word_text and word_text not in ("", ".") and len(word_text) > 1:
                valid_words.append(w)

        if len(valid_words) < 2:
            return 75.0, "有效词数不足，无法分析连读", viz_data

        # 分析每个相邻词对
        pair_results = []
        gaps = []
        linkable_count = 0
        linked_count = 0

        for i in range(len(valid_words) - 1):
            w_cur = valid_words[i]
            w_next = valid_words[i + 1]
            gap = w_next.get("start", 0) - w_next.get("end", 0)  # fallback
            gap = w_next["start"] - w_cur["end"]
            gap_ms = round(gap * 1000)
            gaps.append(gap_ms)

            # G2P 获取两个词的音素
            try:
                cur_phonemes = self.g2p(w_cur["word"].lower().strip())
                next_phonemes = self.g2p(w_next["word"].lower().strip())
            except Exception:
                cur_phonemes = []
                next_phonemes = []

            last_ph = cur_phonemes[-1] if cur_phonemes else "?"
            first_ph = next_phonemes[0] if next_phonemes else "?"
            last_type = self._classify_phoneme(last_ph)
            first_type = self._classify_phoneme(first_ph)
            is_linkable = last_type == "consonant" and first_type == "vowel"

            if is_linkable:
                linkable_count += 1
                # 辅元连读条件存在，按 gap 评分
                if gap_ms <= 30:
                    pair_score = 90 + (30 - gap_ms) / 3  # 90-100
                    linked_count += 1
                elif gap_ms <= 80:
                    pair_score = 70 + (80 - gap_ms) / 5  # 70-90
                elif gap_ms <= 150:
                    pair_score = 40 + (150 - gap_ms) / 3.5  # 40-70
                else:
                    pair_score = max(0, 40 - (gap_ms - 150) / 10)
            else:
                # 无连读条件，该词对不评判
                pair_score = 100.0

            pair_score = round(min(max(pair_score, 0), 100))

            pair_results.append({
                "word_pair": f"{w_cur['word']} {w_next['word']}",
                "linkable": is_linkable,
                "last_phoneme": last_ph,
                "first_phoneme": first_ph,
                "gap_ms": gap_ms,
                "score": pair_score,
            })

        # 计算综合得分
        avg_gap = round(sum(gaps) / len(gaps), 1) if gaps else 0
        viz_data = {
            "pairs": pair_results,
            "linkable_count": linkable_count,
            "linked_count": linked_count,
            "avg_gap_ms": avg_gap,
        }

        if linkable_count == 0:
            # 没有连读条件，不影响评分
            return 80.0, "未检测到辅音-元音连读条件，此项不适用", viz_data

        linkable_scores = [p["score"] for p in pair_results if p["linkable"]]
        avg_linking_score = sum(linkable_scores) / len(linkable_scores) if linkable_scores else 80.0
        linking_score = round(min(max(avg_linking_score, 0), 100))

        # 生成分析说明
        linked_ratio = linked_count / linkable_count if linkable_count > 0 else 0
        if linked_ratio >= 0.8:
            detail = f"连读自然流畅，{linked_count}/{linkable_count} 处连读到位，平均间隙 {avg_gap:.0f}ms"
        elif linked_ratio >= 0.5:
            detail = f"部分连读到位，{linked_count}/{linkable_count} 处连读，{linkable_count - linked_count} 处可以更连贯"
        elif linked_ratio >= 0.2:
            detail = f"连读偏少，{linkable_count} 处可连读但仅 {linked_count} 处连上，建议多听母语者发音"
        else:
            detail = f"基本没有连读，{linkable_count} 处可连读均未连上，像在逐个蹦词"

        if avg_gap > 150:
            detail += "；词间停顿较长，整体节奏偏慢"

        return linking_score, detail, viz_data

    def score(self, audio_path: str, text: str) -> Dict:
        """
        对音频进行发音评测

        Args:
            audio_path: 音频文件路径（16kHz 单声道 WAV）
            text: 标准文本

        Returns:
            包含 overall, dimensions, errors, char_scores 的评测结果
        """
        if not self._loaded:
            raise RuntimeError("模型未加载，请先调用 load()")

        # 音频 → 特征
        emission, waveform = self._extract_features(audio_path)

        # G2P: 文本 → 音素
        phonemes = self._text_to_phonemes(text)
        logger.info(f"文本: {text} → 音素: {' '.join(phonemes)}")

        # CTC 强制对齐
        target_indices, alignments, log_prob, best_path = self._ctc_forced_alignment(
            emission, text
        )

        if not alignments:
            return {
                "overall": 0.0,
                "dimensions": [{"label": "音素准确度", "score": 0.0}],
                "errors": [{"phoneme": "N/A", "actual": "无法对齐", "tip": "请检查音频质量和文本是否匹配"}],
            }

        # GOP 评分
        char_scores, avg_score = self._compute_gop_scores(
            target_indices, alignments, log_prob
        )

        # 错误音素分析
        errors = self._generate_error_tips(char_scores, text)

        # 重音位置分析
        phonemes = self._text_to_phonemes(text)
        stress_score, stress_detail, stress_viz = self._analyze_stress(
            audio_path, alignments, target_indices, phonemes
        )

        # 语调曲线分析
        intonation_score, intonation_detail, intonation_viz = self._analyze_intonation(
            audio_path, text
        )

        # 连读表现分析
        linking_score, linking_detail, linking_viz = self._analyze_linking(
            audio_path, text
        )

        # 五维评分
        accuracy_score = min(round(avg_score), 100)
        dimensions = [
            {"label": "音素准确度", "score": accuracy_score},
            {"label": "重音位置", "score": stress_score},
            {"label": "语调曲线", "score": intonation_score},
            {"label": "连读表现", "score": linking_score},
            {"label": "流利度", "score": 0},    # 待实现（语速+停顿分析）
        ]

        # 综合分 = 已有维度的加权平均
        active_scores = [accuracy_score, stress_score, intonation_score, linking_score]
        overall = round(sum(active_scores) / len(active_scores))

        return {
            "overall": overall,
            "dimensions": dimensions,
            "errors": errors,
            "char_scores": char_scores,
            "analysis_detail": {
                "stress": stress_detail,
                "intonation": intonation_detail,
                "linking": linking_detail,
            },
            "stress_viz": stress_viz,
            "intonation_viz": intonation_viz,
            "linking_viz": linking_viz,
        }

    def score_sync(self, audio_path: str, text: str) -> Dict:
        """同步版本的 score（供 run_in_executor 使用）"""
        return self.score(audio_path, text)


async def score_audio(audio_path: str, text: str) -> Dict:
    """异步接口：在线程池中运行发音评测"""
    service = get_pronunciation_service()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, service.score_sync, audio_path, text)


def get_pronunciation_service() -> PronunciationService:
    """获取全局发音评测服务单例"""
    global _service_instance
    if _service_instance is None:
        from app.core.config import settings

        _service_instance = PronunciationService(
            device=settings.pronunciation_device
        )
        _service_instance.load()
    return _service_instance
