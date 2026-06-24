# 模块 4：AI 发音评测与纠错

> 实现日期：2026-05 ~ 2026-06
> 技术栈：wav2vec2 + GOP + CTC 强制对齐 + WhisperX + PyTorch (MPS)

---

## 1. 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                             │
│  PronunciationView.vue                                       │
│  - 录音上传 → 展示五维评分 → 可视化波形/音高/音素             │
└──────────────┬───────────────────────────────────────────────┘
               │ POST /api/pronunciation/score
               │ (multipart: audio + text + mode)
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              PronunciationService (单例)               │   │
│  │                                                      │   │
│  │  Step 1: 特征提取 (wav2vec2 Base)                     │   │
│  │  Step 2: 文本→音素 (g2p-en)                          │   │
│  │  Step 3: CTC 强制对齐 (维特比解码)                     │   │
│  │  Step 4: GOP 评分 (音素准确度)                        │   │
│  │  Step 5: 错误分析 (发音纠正提示)                       │   │
│  │  Step 6: 重音分析 (RMS 能量包络)                      │   │
│  │  Step 7: 语调分析 (F0 基频 + 趋势拟合)                │   │
│  │  Step 8: 连读分析 (WhisperX + G2P 辅音-元音)          │   │
│  │  Step 9: 节奏分析 (音素时长 CV)                        │   │
│  │  Step 10: 综合聚合 (加权求和)                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │ ProfileUpdater    │  │ Edge TTS                     │     │
│  │ 分数持久化 + EMA  │  │ POST /reference-audio        │     │
│  └──────────────────┘  └──────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 评分流水线（10 步）

### 模型加载

应用启动时通过 FastAPI lifespan 预加载模型：

| 模型 | 用途 | 说明 |
|------|------|------|
| **wav2vec2 Base** | 特征提取 | `WAV2VEC2_ASR_BASE_960H`，95M 参数，LibriSpeech 960h 微调 |
| **WhisperX small** | 词级时间戳 | int8 精度，用于连读分析 |
| **g2p-en** | 文本→音素 | ARPABET 音素序列 |

设备选择：Apple Silicon 自动使用 MPS，WhisperX 在 MPS 上回退到 CPU（稳定性原因）。

### Step 1: 特征提取 `_extract_features()`

```python
# 输入：16kHz WAV 音频
# 输出：log_softmax 后验概率 (1, T, num_labels)
# T = 帧数（每帧约 20ms）
# num_labels = CTC 标签数（A-Z, ', |, 特殊标记）
```

### Step 2: 文本→音素 `_text_to_phonemes()`

```python
# 输入："hello world"
# 输出：["HH", "AH", "L", "OW", "W", "ER", "L", "D"]
```

### Step 3: CTC 强制对齐 `_ctc_forced_alignment()`

**维特比动态规划**，将音素序列对齐到音频帧：

```
CTC 扩展状态：[blank, p1, blank, p2, blank, ..., blank]

DP 允许三种转移：
  - 停留（同一 CTC 状态）
  - 前进 1（到下一个状态）
  - 前进 2（跳过 blank，允许相同音素重复）

输出：(音素索引, 对齐区间 [(start_frame, end_frame), ...], log_prob, best_path)
```

### Step 4: GOP 评分 `_compute_gop_scores()`

**发音良好度 (Goodness of Pronunciation)**：

```python
for each aligned phoneme p in interval [start, end]:
    avg_log_prob = mean(log_prob[start:end, index_of(p)])
    gop_score = exp(avg_log_prob) * 100  # 0-100
```

评级阈值：
| GOP 分数 | 评级 |
|----------|------|
| > 80 | 优秀 |
| > 60 | 良好 |
| > 40 | 一般 |
| ≤ 40 | 需练习 |

### Step 5: 错误分析 `_generate_error_tips()`

- 标记 GOP < 55 的音素
- 通过 ~30 个 ARPABET 音素的字典提供中文发音纠正提示
- 最多返回 5 个错误

### Step 6: 重音分析 `_analyze_stress()`

基于 RMS 能量包络分析：

```python
energy_cv = 变异系数(各音素归一化能量)

if energy_cv < 0.05:   score = 30 + energy_cv * 200   # 太平坦
elif energy_cv < 0.15:  score = 50 + (cv-0.05)*300    # 轻微变化
elif energy_cv < 0.40:  score = 70 + (cv-0.15)*80     # 自然 ✓
elif energy_cv < 0.80:  score = 90 - (cv-0.40)*50     # 过度
else:                   score = 60                      # 极端
```

重音标记：`RMS energy > mean_energy × 1.3`

### Step 7: 语调分析 `_analyze_intonation()`

使用 librosa `pyin` 提取 F0 基频，按句子类型评分：

| 句子类型 | 最佳特征 | 评分规则 |
|----------|----------|----------|
| 陈述句 | 降调 -2.0 ~ -0.3 半音/秒 | 峰值 85 分 |
| 疑问句 | 升调 > 0.5 半音/秒 | 峰值 85 分 |
| 感叹句 | 音高范围 > 5 半音 | 80 分，否则 55 |

### Step 8: 连读分析 `_analyze_linking()`

使用 WhisperX 词级时间戳 + G2P 音素分类：

```python
for each adjacent word pair (w1, w2):
    if w1 以辅音结尾 AND w2 以元音开头:  # 可连读
        gap = w2.start - w1.end (ms)
        gap <= 30ms:  score = 90-100  (优秀连读)
        gap <= 80ms:  score = 70-90   (良好)
        gap <= 150ms: score = 40-70   (一般)
        gap > 150ms:  score = 0-40    (未连读)
```

### Step 9: 节奏分析 `_analyze_rhythm()`

基于音素时长变异系数 (CV = std/mean)：

```python
CV < 0.15:   score = 70          # 太均匀（缺乏 stress-timed 特征）
CV 0.15-0.30: score = 88-21      # 自然范围 ✓
CV 0.30-0.50: score = 75-50      # 可接受
CV 0.50-0.80: score = 55-20      # 不稳定
CV > 0.80:    score = 35          # 严重不均匀

# 异常停顿扣分
for each pause (duration > 2× mean):
    score -= 8 (最多扣 30 分)
```

### Step 10: 综合聚合 `score()`

发音服务通过 `ThreadPoolExecutor(max_workers=2)` 异步执行，避免阻塞主线程。

---

## 3. 五维评分权重

### 单词模式 (mode="word")

| 维度 | 权重 | 标签 |
|------|------|------|
| 音素准确度 | **50%** | 音素准确度 |
| 重音位置 | **25%** | 重音位置 |
| 节奏感 | **25%** | 节奏感 |
| 语调曲线 | 0% | — |
| 连读表现 | 0% | — |

### 句子模式 (mode="sentence")

| 维度 | 权重 | 标签 |
|------|------|------|
| 音素准确度 | **40%** | 音素准确度 |
| 重音位置 | **15%** | 重音位置 |
| 连读表现 | **15%** | 连读表现 |
| 语调曲线 | **15%** | 语调曲线 |
| 节奏感 | **15%** | 节奏感 |

---

## 4. 可视化数据

每个维度都返回前端可视化所需的详细数据：

### 重音可视化 (StressVizData)
```json
{
  "chars": ["h", "e", "l", "l", "o"],
  "energies": [0.3, 0.5, 0.8, 0.4, 0.2],
  "durations": [80, 120, 150, 100, 90],
  "is_stressed": [false, false, true, false, false],
  "energy_cv": 0.35,
  "dur_cv": 0.22
}
```

### 语调可视化 (IntonationVizData)
```json
{
  "f0_points": [120, 125, 130, 128, 115],  // 最多 50 个采样点
  "direction": "↘",
  "semitones_range": 3.2,
  "sentence_type": "陈述句",
  "slope_st_per_sec": -1.5
}
```

### 连读可视化 (LinkingVizData)
```json
{
  "pairs": [
    {"word_pair": "think about", "linkable": true, "gap_ms": 25, "score": 92}
  ],
  "linkable_count": 3,
  "linked_count": 2,
  "avg_gap_ms": 45
}
```

### 节奏可视化 (RhythmVizData)
```json
{
  "durations_ms": [80, 120, 150, 100, 90, 300, 85],
  "chars": ["h", "e", "l", "l", "o", " ", "w"],
  "mean": 120,
  "std": 65,
  "cv": 0.54,
  "pause_count": 1,
  "is_pause": [false, false, false, false, false, true, false]
}
```

---

## 5. API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pronunciation/score` | 上传音频+文本+模式，返回五维评分 + 可视化数据 |
| POST | `/api/pronunciation/reference-audio` | 生成参考音频（Edge TTS），返回 MP3 流 |

### 请求参数

```
POST /api/pronunciation/score
  - audio: UploadFile (WAV/WebM/MP3)
  - text: str (参考文本)
  - mode: str ("word" | "sentence")
  - Authorization: Bearer <token>
```

### 响应结构

```json
{
  "overall_score": 72.5,
  "overall_level": "良好",
  "dimensions": [
    {"label": "音素准确度", "score": 78.0, "level": "良好", "comment": "..."},
    {"label": "重音位置", "score": 65.0, "level": "良好", "comment": "..."},
    {"label": "语调曲线", "score": 70.0, "level": "良好", "comment": "..."},
    {"label": "连读表现", "score": 55.0, "level": "一般", "comment": "..."},
    {"label": "节奏感", "score": 82.0, "level": "优秀", "comment": "..."}
  ],
  "error_phonemes": [
    {"phoneme": "TH", "score": 42.0, "tip": "舌尖放在上下齿之间，轻咬舌尖"}
  ],
  "stress_viz": {...},
  "intonation_viz": {...},
  "linking_viz": {...},
  "rhythm_viz": {...}
}
```

---

## 6. 分数持久化

发音评分后，5 个维度分数通过 `ProfileUpdater` 写入数据库：

```
音素准确度 → phoneme_accuracy → speaking
重音位置   → stress           → speaking
语调曲线   → intonation       → speaking
连读表现   → linking          → speaking
节奏感     → rhythm           → speaking
```

每次写入后自动触发 EMA 重算，更新 `user_profiles.level_final`。

---

## 7. 参考音频生成

使用 **Edge TTS**（微软免费 TTS）生成标准发音参考：

```
POST /api/pronunciation/reference-audio
  - text: "Hello, how are you?"
  - voice: "en-US-JennyNeural" (默认)

返回: audio/mpeg 流
```

支持 4 种音色，SSML 控速，句级时间戳。

---

## 8. 文件清单

| 文件 | 说明 |
|------|------|
| `backend/app/services/pronunciation.py` | 核心发音服务（wav2vec2 + GOP + CTC + 五维分析） |
| `backend/app/api/pronunciation.py` | 发音 API 路由（评分 + 参考音频） |
| `backend/app/schemas/pronunciation.py` | 发音 Pydantic Schema（请求/响应/可视化数据） |
| `backend/app/services/asr.py` | WhisperX ASR 服务（连读分析 + 对话转录） |
| `backend/app/services/tts.py` | Edge TTS 服务（参考音频生成） |
| `backend/app/services/profile_updater.py` | 分数持久化 + EMA 画像更新 |
| `backend/app/models/profile.py` | UserSkillScore ORM |
| `backend/app/core/config.py` | pronunciation_device 配置 |
| `backend/main.py` | 模型预加载 + 路由注册 |
| `backend/test_pronunciation.py` | 端到端测试脚本 |
| `frontend/src/views/pronunciation/` | 前端发音练习页面 |
| `frontend/src/components/pronunciation/` | 前端发音可视化组件 |

---

## 9. 技术要点

- **GOP 算法**：业内标准的发音评分方法，通过对数后验概率衡量每个音素的发音质量
- **CTC 强制对齐**：自实现的维特比解码，不依赖 torchaudio 的强制对齐 API，更灵活可控
- **MPS 加速**：Apple Silicon 上使用 MPS 加速 wav2vec2 推理，WhisperX 回退 CPU 保证稳定性
- **异步执行**：评分在 ThreadPoolExecutor 中运行，不阻塞 FastAPI 事件循环
- **五维评分**：不仅评音素准确度，还评重音、语调、连读、节奏，全方位覆盖口语能力