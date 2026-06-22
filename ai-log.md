# AI 操作日志

---

## 2026-06-22 — 对话评分综合报告（v2 丰富版）

**变更摘要：**
- 后端 Schema 新增 `utterances`、`transcript`、`text_dimension_details`、`scoring_methodology` 字段
- LLM 评分提示升级：每个维度返回 `feedback`、`strengths`、`weaknesses` 详细评语，max_tokens 增至 800
- `/end` 端点保留每句话的完整发音评分结果（含 viz 可视化数据），返回对话记录和方法论说明
- 新建 `UtteranceDetailPanel.vue` 共享组件：逐音素评分表、重音能量图、语调 F0 曲线、连读词对表、节奏时长图、算法说明
- 前端报告页重构为多节可滚动布局：综合分+方法论 → 语音评测(平均维度+错误音素+逐句详情) → 文本评测(LLM详细卡片) → 对话记录 → 改进建议

**新增文件：**
- `frontend/src/components/pronunciation/UtteranceDetailPanel.vue`

**修改文件：**
- `backend/app/schemas/conversation.py` — ConversationEndResponse 新增 4 字段
- `backend/app/services/llm.py` — score_conversation 提示升级 + max_tokens 800
- `backend/app/api/conversation.py` — /end 端点保留完整数据
- `frontend/src/views/conversation/VoiceCallView.vue` — 报告 UI 全面重构

---

## 2026-06-22 — AI 智能对话全屏路由 + 阿里百炼接入 + ASR/TTS 服务

**变更摘要：**
- 后端配置将 `deepseek_api_key` 替换为 `bailian_api_key`，切换至阿里百炼 DashScope
- 后端 `main.py` 注册对话路由 `/api/conversation`
- 新建 ASR 服务（WhisperX 转录 + 词级时间戳）和 TTS 服务（Edge TTS 语音合成）
- 前端对话路由从学习布局子路由改为独立全屏路由，导航栏名称改为「AI 智能对话」
- 删除旧的 `ConversationView.vue`，由 `VoiceCallView.vue` 替代

**新增文件：**
- `backend/app/services/asr.py` — WhisperX 语音识别服务
- `backend/app/services/tts.py` — Edge TTS 语音合成服务
- `docs/introduction.md` — 项目介绍文档
- `docs/prds/lingolab-ai-v1.2-prd.md` — v1.2 PRD

**修改文件：**
- `backend/app/core/config.py` — deepseek → bailian
- `backend/main.py` — 注册 conversation 路由
- `frontend/src/router/index.js` — 对话路由改为独立全屏路由
- `frontend/src/components/layout/TopNavLayout.vue` — 导航文字「AI 对话」→「AI 智能对话」
- `frontend/src/components.d.ts` — 添加 UtteranceDetailPanel 类型声明

**删除文件：**
- `frontend/src/views/conversation/ConversationView.vue` — 被 VoiceCallView.vue 替代