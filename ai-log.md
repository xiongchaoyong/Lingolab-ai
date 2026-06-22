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