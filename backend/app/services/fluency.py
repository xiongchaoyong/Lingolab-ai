"""流利度评估服务 — 基于 ASR 词级时间戳 + LLM 语义分析

五维评分体系（SRS 3.3.3）：
  维度1 语速(wpm)         — 算法计算，满分25
  维度2 停顿频率           — 算法计算，满分20
  维度3 重复率             — 算法计算，满分20
  维度4 语法正确性          — LLM 评估，满分20
  维度5 内容相关性          — LLM 评估，满分15

分段评级：85-100 优秀 / 70-84 良好 / 55-69 中等 / 40-54 初级 / <40 入门
"""

import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_fluency_grade(score: float) -> str:
    """流利度分段评级"""
    if score >= 85:
        return "优秀"
    elif score >= 70:
        return "良好"
    elif score >= 55:
        return "中等"
    elif score >= 40:
        return "初级"
    return "入门"


def _count_words(text: str) -> int:
    """统计英文单词数"""
    return len(text.strip().split())


def _detect_repetitions(text: str) -> float:
    """检测文本中的重复词/短语比例

    检测连续重复词 + 2-gram 重复，返回重复比例 (0.0-1.0)
    """
    words = text.strip().lower().split()
    if len(words) < 3:
        return 0.0

    repeated_count = 0

    # 连续重复词检测
    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repeated_count += 1

    # 2-gram 重复检测（检测不自然的短语重复）
    if len(words) >= 4:
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
        seen_bigrams = {}
        for i, bg in enumerate(bigrams):
            if bg in seen_bigrams and i - seen_bigrams[bg] <= 3:
                repeated_count += 1
            else:
                seen_bigrams[bg] = i

    return min(repeated_count / len(words), 1.0)


def assess_algorithmic(
    text: str,
    words: List[Dict],
    audio_duration: float,
) -> Dict:
    """
    算法流利度计算 — 维度 1-3

    Args:
        text: ASR 转写文本
        words: WhisperX 词级时间戳 [{"word": "hello", "start": 0.1, "end": 0.5, "score": 0.98}, ...]
        audio_duration: 音频实际时长（秒），用于兜底

    Returns:
        {
            "wpm": {"score": 22, "value": 110, "max": 25},
            "pause_frequency": {"score": 18, "pauses_per_min": 3.2, "max": 20},
            "repetition": {"score": 19, "rate": 0.03, "max": 20},
            "overall": 59,  # 维度1-3 综合分
        }
    """
    word_count = _count_words(text)

    # 计算实际说话时长（从第一个词到最后一个词）
    if words and len(words) >= 2:
        speaking_start = words[0].get("start", 0)
        speaking_end = words[-1].get("end", audio_duration)
        speaking_duration = speaking_end - speaking_start
    else:
        speaking_duration = audio_duration

    if speaking_duration <= 0:
        speaking_duration = 1.0  # 兜底

    duration_minutes = speaking_duration / 60.0

    # ── 维度1：语速 (wpm) ──
    wpm = word_count / duration_minutes if duration_minutes > 0 else 0

    # 理想语速 100-120 wpm（英语学习者），偏差按比例扣分
    if 100 <= wpm <= 120:
        wpm_score = 25
    elif wpm < 100:
        wpm_score = max(0, round(25 * (wpm / 100)))
    else:
        wpm_score = max(0, round(25 * (120 / wpm)))

    # ── 维度2：停顿频率 ──
    pause_count = 0
    if words and len(words) >= 2:
        for i in range(1, len(words)):
            gap = words[i].get("start", 0) - words[i - 1].get("end", 0)
            if gap > 0.5:
                pause_count += 1

    pauses_per_min = pause_count / duration_minutes if duration_minutes > 0 else 0

    # <2 次/分钟为满分，<5 次/分钟良好，>10 次/分钟为差
    if pauses_per_min <= 2:
        pause_score = 20
    elif pauses_per_min <= 5:
        pause_score = 16
    elif pauses_per_min <= 8:
        pause_score = 12
    elif pauses_per_min <= 10:
        pause_score = 8
    else:
        pause_score = max(0, round(20 * (2 / pauses_per_min)))

    # ── 维度3：重复率 ──
    repetition_rate = _detect_repetitions(text)

    if repetition_rate <= 0.05:
        rep_score = 20
    elif repetition_rate <= 0.10:
        rep_score = 16
    elif repetition_rate <= 0.15:
        rep_score = 12
    elif repetition_rate <= 0.20:
        rep_score = 8
    else:
        rep_score = max(0, round(20 * (0.05 / repetition_rate)))

    algorithmic_overall = wpm_score + pause_score + rep_score

    result = {
        "wpm": {
            "score": wpm_score,
            "value": round(wpm, 1),
            "max": 25,
            "label": "语速",
            "detail": f"{wpm:.0f} 词/分钟",
        },
        "pause_frequency": {
            "score": pause_score,
            "pauses_per_min": round(pauses_per_min, 1),
            "pause_count": pause_count,
            "max": 20,
            "label": "停顿控制",
            "detail": f"停顿 {pause_count} 次 ({pauses_per_min:.1f}次/分钟)",
        },
        "repetition": {
            "score": rep_score,
            "rate": round(repetition_rate, 3),
            "max": 20,
            "label": "表达流畅度",
            "detail": f"重复率 {repetition_rate:.0%}",
        },
        "overall": algorithmic_overall,
    }

    logger.debug(
        f"算法流利度: wpm={wpm:.0f}({wpm_score}/25), "
        f"pauses={pauses_per_min:.1f}/min({pause_score}/20), "
        f"rep={repetition_rate:.2%}({rep_score}/20)"
    )

    return result


def aggregate_fluency(round_scores: List[Dict]) -> Dict:
    """
    汇总多轮流利度分数

    Args:
        round_scores: 每轮的算法流利度结果列表

    Returns:
        {
            "overall": 78,
            "grade": "良好",
            "rounds": [...],
            "best_round": 3,
            "dimension_averages": {...},
        }
    """
    if not round_scores:
        return {
            "overall": 0,
            "grade": "入门",
            "rounds": [],
            "best_round": None,
            "dimension_averages": {},
        }

    # 各维度汇总
    all_wpm = []
    all_pause = []
    all_rep = []
    enriched_rounds = []

    for i, rs in enumerate(round_scores):
        wpm_d = rs.get("wpm", {})
        pause_d = rs.get("pause_frequency", {})
        rep_d = rs.get("repetition", {})
        llm_d = rs.get("llm", {})

        wpm_score = wpm_d.get("score", 0)
        pause_score = pause_d.get("score", 0)
        rep_score = rep_d.get("score", 0)
        grammar_score = llm_d.get("grammar", {}).get("score", 0)
        relevance_score = llm_d.get("relevance", {}).get("score", 0)

        all_wpm.append(wpm_score)
        all_pause.append(pause_score)
        all_rep.append(rep_score)

        round_total = wpm_score + pause_score + rep_score + grammar_score + relevance_score

        enriched_rounds.append({
            "round": i + 1,
            "text": rs.get("text", ""),
            "wpm": wpm_d,
            "pause_frequency": pause_d,
            "repetition": rep_d,
            "grammar": llm_d.get("grammar", {}),
            "relevance": llm_d.get("relevance", {}),
            "total": round_total,
        })

    # 综合分 = 各轮平均
    all_round_totals = [r["total"] for r in enriched_rounds]
    overall = round(sum(all_round_totals) / len(all_round_totals))
    grade = _get_fluency_grade(overall)

    # 最佳轮次
    best_round = max(enriched_rounds, key=lambda r: r["total"])["round"]

    # 维度平均
    dimension_averages = {
        "wpm_avg": round(sum(all_wpm) / len(all_wpm), 1) if all_wpm else 0,
        "pause_avg": round(sum(all_pause) / len(all_pause), 1) if all_pause else 0,
        "repetition_avg": round(sum(all_rep) / len(all_rep), 1) if all_rep else 0,
    }

    return {
        "overall": overall,
        "grade": grade,
        "rounds": enriched_rounds,
        "best_round": best_round,
        "dimension_averages": dimension_averages,
    }