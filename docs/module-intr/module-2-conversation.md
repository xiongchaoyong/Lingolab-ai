# 模块 6：智能语音对话练习

> 实现日期：2026-05 ~ 2026-06
> 技术栈：WhisperX (ASR) → 阿里百炼 qwen-plus (LLM) → Edge TTS + SSE 流式

---

## 1. 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                             │
│  ConversationView.vue                                        │
│  - 选择场景 → 录音 → SSE 流式接收 AI 回复 → TTS 播放          │
└──────────────┬───────────────────────────────────────────────┘
               │ POST /api/conversation/stream/speak (SSE)
               │ POST /api/conversation/tts
               │ POST /api/conversation/end
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  对话管线 (ASR → LLM → TTS)            │   │
│  │                                                      │   │
│  │  用户音频上传                                          │   │
│  │     │                                                │   │
│  │     ▼                                                │   │
│  │  ffmpeg 转码 (16kHz WAV)                              │   │
│  │     │                                                │   │
│  │     ▼                                                │   │
│  │  WhisperX ASR → 转录文本 + 词级时间戳                  │   │
│  │     │                                                │   │
│  │     ▼                                                │   │
│  │  追加到会话历史 [user, ai, user, ai, ...]              │   │
│  │     │                                                │   │
│  │     ▼                                                │   │
│  │  阿里百炼 qwen-plus → AI 回复 (流式 SSE)               │   │
│  │     │                                                │   │
│  │     ▼                                                │   │
│  │  Edge TTS → 合成语音 → 返回音频                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │ 会话管理 (内存)    │  │ 双层评分 (/end)               │     │
│  │ _sessions dict   │  │ 语音: wav2vec2+GOP (50%)     │     │
│  │ 场景 + 历史 + 轮次 │  │ 文本: LLM评分 (50%)         │     │
│  └──────────────────┘  └──────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 对话场景

### 4 个自由对话场景

| 场景标识 | 名称 | AI 角色 | CEFR 范围 |
|----------|------|---------|-----------|
| `self_intro` | 自我介绍与日常问候 | Alex，友好的英语对话伙伴 | A1-B2 |
| `directions` | 问路指路 | 问路的游客 | A2-B2 |
| `shopping` | 购物消费 | 服装店店员 | A2-B2 |
| `restaurant` | 餐厅点餐 | 餐厅服务员 | A2-B2 |

### 3 个角色扮演场景

| 场景标识 | 名称 | AI 角色 |
|----------|------|---------|
| `interviewee` | 工作面试 | 面试官 |
| `waiter` | 餐厅服务 | 顾客 |
| `guide` | 景点导游 | 游客 |

---

## 3. ASR → LLM → TTS 管线

### 3.1 单步流程（非流式 `/speak`）

```
1. 音频上传 → 保存为临时文件 (.webm)
2. ffmpeg 转码 → 16kHz 单声道 16-bit PCM WAV
3. WhisperX 转录 → 文本 + 词级时间戳
4. 空语音检测 → 如未识别，返回回退消息
5. 追加用户消息到会话历史
6. LLM 生成回复 → 传入场景 + 历史 + CEFR 等级
7. 返回 AI 文本（音频由前端单独请求 /tts）
```

### 3.2 SSE 流式流程 (`/stream/speak`)

**服务器端**：异步生成器产生 SSE 事件

```
事件类型:
  asr   → data: {"type": "asr", "text": "用户说的文本"}
  token → data: {"type": "token", "content": "That"}
  token → data: {"type": "token", "content": " sounds"}
  token → data: {"type": "token", "content": " great"}
  done  → data: {"type": "done", "full_text": "...", "session_id": "..."}
  error → data: {"type": "error", "message": "..."}
```

**LLM 流式集成**：
```python
async with httpx.AsyncClient.stream(
    "POST",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    json={"model": "qwen-plus", "stream": True, "messages": [...]},
    headers={"Authorization": f"Bearer {api_key}"},
) as response:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            chunk = json.loads(line[6:])
            if chunk == "[DONE]":
                break
            content = chunk["choices"][0]["delta"]["content"]
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
```

**前端消费**：
1. 连接 SSE 端点
2. 监听 `asr` → 显示转录文本
3. 监听 `token` → 逐字显示 AI 回复
4. 监听 `done` → 获取完整文本 + 会话 ID
5. 关闭连接

### 3.3 TTS 语音合成

使用 **Edge TTS**（微软免费），支持 4 种音色：
- `en-US-JennyNeural`（默认，女声）
- `en-US-GuyNeural`（男声）
- `en-US-AriaNeural`（女声）
- `en-US-DavisNeural`（男声）

SSML 控速，句级时间戳，返回 MP3 流。

---

## 4. 会话管理

### 进程内存储

```python
_sessions: dict[str, dict] = {
    "uuid-xxxx": {
        "scene": "self_intro",
        "cefr_level": "B1",
        "history": [
            {"role": "ai", "text": "Hi! I'm Alex. How are you today?"},
            {"role": "user", "text": "I'm fine, thank you."},
            {"role": "ai", "text": "That's great! What do you like to do?"},
            ...
        ],
        "round": 3,                    # 当前轮次
        "user_audios": [               # 音频路径 (用于结束评分)
            ("/tmp/xxx.wav", "I'm fine, thank you."),
            ...
        ],
    }
}
```

### 会话生命周期

```
POST /stream/start → 创建会话，返回 session_id + AI 开场白
    ↓
POST /stream/speak → 每轮对话（最多 6 轮）
    ↓  (round >= 6 → conversation_complete = true)
    ↓
POST /end → 双层评分 → 持久化分数 → 清理会话 + 临时文件
```

- `MAX_CONVERSATION_ROUNDS = 6`
- 会话存储在内存中（生产环境应迁移至 Redis）
- 结束时清理临时 WAV 文件 + 删除会话

---

## 5. LLM 提示词系统

### 5.1 场景提示词

```python
SCENE_PROMPTS = {
    "self_intro": "你是 Alex，一个友好的英语对话伙伴。你正在和一位新朋友聊天...",
    "restaurant": "你是一家餐厅的服务员。客人正在点餐...",
    "shopping": "你是一家服装店的店员。顾客正在挑选衣服...",
    "directions": "你是一个正在问路的游客。你在寻找附近的景点...",
}
```

### 5.2 CEFR 难度适配

```python
CEFR_DIFFICULTY = {
    "A1": "使用非常简单的单词和短句。语速要慢。",
    "A2": "使用简单的日常词汇。保持句子简短。",
    "B1": "使用中级词汇，可以适当使用短语动词和习语。",
    "B2": "使用高级词汇，以正常语速自然交流。",
}
```

系统提示 = `场景提示词.format(level=cefr)` + 难度指令 + 固定后缀：
> "每次变换措辞——切勿重复相同的开场白或问题。回复中不要使用表情符号或特殊符号——仅使用纯英文文本。"

### 5.3 LLM 方法

| 方法 | 用途 | temperature | max_tokens |
|------|------|-------------|------------|
| `chat()` | 对话回复生成 | 0.9 | 150 |
| `chat_stream()` | 流式对话回复 | 0.9 | 150 |
| `chat_roleplay()` | 角色扮演回复 | 0.9 | 150 |
| `chat_roleplay_stream()` | 角色扮演流式 | 0.9 | 150 |
| `score_conversation()` | 对话文本评分 | 0.3 | 800 |
| `score_roleplay()` | 角色扮演评分 | 0.3 | 800 |

高温度 (0.9) 用于生成多样化回复，低温度 (0.3) 用于评分保证一致性。

### 5.4 回退机制

所有 LLM 方法包含 try/except：
- API 401 → 提示 API Key 配置错误
- 其他错误 → 返回友好回退消息 "Sorry, I'm a bit confused right now. Could you repeat that?"
- 评分失败 → 返回默认 75 分 + 占位反馈

---

## 6. 双层评分系统

### 对话结束时 (`POST /end`)

**第 1 层：语音评分（wav2vec2 + GOP）**
- 对每轮用户音频调用 `PronunciationService.score(mode="sentence")`
- 返回五维分数：音素准确度、重音位置、语调曲线、连读表现、节奏感
- 每维度取所有轮次平均

**第 2 层：文本评分（LLM）**
- 调用 `llm.score_conversation(history, cefr_level)`
- 三个维度：

| 维度 | 说明 |
|------|------|
| 语法正确率 | 句式是否准确，时态语态是否正确 |
| 词汇丰富度 | 用词是否多样，是否使用了恰当级别的词汇 |
| 对话参与度 | 是否主动推进对话，回应是否自然 |

**综合分数**：
```
综合分 = 语音平均分 × 0.5 + 文本平均分 × 0.5
```

### 角色扮演评分（60/40 权重）

```
综合分 = 角色维度 × 0.6 + 发音 × 0.4
```

角色维度（LLM 评分）：
- 角色贴合度
- 场景礼仪
- 专业术语
- 应对能力

### 分数持久化

评分结果通过 `ProfileUpdater.ingest_conversation_scores()` 写入数据库：

| 来源 | 维度 | 映射 |
|------|------|------|
| 语音 5 维 | conversation:pronunciation:音素准确度 | speaking |
| 语音 5 维 | conversation:pronunciation:重音位置 | speaking |
| ... | ... | speaking |
| 文本 3 维 | conversation:text:语法正确率 | grammar |
| 文本 3 维 | conversation:text:词汇丰富度 | reading |
| 文本 3 维 | conversation:text:对话参与度 | speaking |

写入后自动触发 EMA 重算。

---

## 7. API 接口

### 自由对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/conversation/stream/start` | 开始对话，返回 AI 开场白（SSE 流式） |
| POST | `/api/conversation/stream/speak` | 上传音频，返回 ASR + LLM 回复（SSE 流式） |
| POST | `/api/conversation/speak` | 上传音频，返回 AI 回复（非流式） |
| POST | `/api/conversation/tts` | 文本转语音 |
| POST | `/api/conversation/end` | 结束对话，返回双层评分 |
| GET | `/api/conversation/sessions/{id}` | 获取会话信息 |

### 角色扮演

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/roleplay/stream/start` | 开始角色扮演 |
| POST | `/api/roleplay/stream/speak` | 角色扮演对话（SSE 流式） |
| POST | `/api/roleplay/end` | 结束角色扮演，返回评分 |

---

## 8. 数据流完整示例

```
用户: 选择场景 "restaurant"，等级 B1
  ↓
POST /stream/start {scene: "restaurant", cefr_level: "B1"}
  → 创建会话 session_id = "abc-123"
  → AI 开场白: "Welcome to our restaurant! May I take your order?"
  ↓
用户: 录音 "I'd like a steak please."
  ↓
POST /stream/speak {session_id: "abc-123", audio: <file>}
  → ffmpeg 转码 → WhisperX 转录: "I'd like a steak please."
  → SSE: {"type": "asr", "text": "I'd like a steak please."}
  → 追加到 history: {role: "user", text: "I'd like a steak please."}
  → LLM 流式: "Great" → " choice!" → " How" → " would" → " you" → " like" → " it" → " cooked?"
  → SSE: {"type": "token", "content": "Great"}, ...
  → SSE: {"type": "done", "full_text": "Great choice! How would you like it cooked?"}
  → 保存音频路径到 session.user_audios
  ↓
用户: 继续对话... (最多 6 轮)
  ↓
POST /end {session_id: "abc-123"}
  → 语音评分: 对 6 段音频逐一评分 → 取平均
  → 文本评分: LLM 评估完整对话历史
  → 综合: 语音×0.5 + 文本×0.5
  → 持久化到 UserSkillScore → EMA 重算
  → 清理临时文件 + 删除会话
```

---

## 9. 文件清单

| 文件 | 说明 |
|------|------|
| `backend/app/api/conversation.py` | 对话 API 路由（6 个端点）+ 会话管理 |
| `backend/app/api/roleplay.py` | 角色扮演 API 路由 |
| `backend/app/schemas/conversation.py` | 对话 Pydantic Schema |
| `backend/app/schemas/roleplay.py` | 角色扮演 Pydantic Schema |
| `backend/app/services/llm.py` | LLM 服务（阿里百炼 + 提示词 + 评分） |
| `backend/app/services/asr.py` | WhisperX ASR 服务 |
| `backend/app/services/tts.py` | Edge TTS 服务 |
| `backend/app/services/pronunciation.py` | 发音评分（对话结束时的语音评分） |
| `backend/app/services/profile_updater.py` | 分数持久化 + EMA 画像更新 |
| `backend/app/models/profile.py` | UserSkillScore ORM |
| `backend/app/core/config.py` | bailian_api_key 配置 |
| `frontend/src/views/conversation/` | 前端对话页面 |
| `frontend/src/api/conversation.js` | 前端对话 API 封装 |

---

## 10. 已知限制

1. **会话存储在内存**中，服务重启丢失，生产环境应迁移至 Redis
2. **LLM 评分依赖外部 API**，网络不稳定时返回默认 75 分
3. **TTS 与 LLM 分离**，前端需额外请求 `/tts` 获取音频（非真正的端到端流式）
4. **对话轮次硬编码为 6 轮**，不支持用户自定义
5. **角色扮演评分**的 60/40 权重为经验值，未经过数据验证