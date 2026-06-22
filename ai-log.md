# AI 操作日志

---

## 2026-06-22 — 对话评分双层体系实现

**变更摘要：**
- 后端 `/end` 端点重构为双层评分：wav2vec2 语音五维评测 + LLM 文本三维评测
- wav2vec2 对会话中每段用户音频调用 `score_audio()`，取五维均分（音素准确度/重音位置/语调曲线/连读表现/节奏感）
- LLM 对对话文本评测三维（语法正确率/词汇丰富度/对话参与度）
- 综合分 = 语音均分 × 0.5 + 文本均分 × 0.5
- 前端报告 UI 改为双分组展示（🎤 语音评测 + 📝 文本评测）

**修改文件：**
- `backend/app/api/conversation.py` — `/end` 端点完全重写
- `frontend/src/views/conversation/VoiceCallView.vue` — 报告 UI 双层分组 + 回退数据格式更新