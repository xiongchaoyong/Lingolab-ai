# AI 操作日志

---

## 2026-06-22 — 角色扮演后端 + 淡紫可爱风 UI 改版 + 路由重构

**变更摘要（拆为两个 commit）：**

### Commit 1 — feat: 角色扮演模块后端 + 前端 API 接入
- 新增角色扮演 LLM 服务：`chat_roleplay` / `chat_roleplay_stream` / `score_roleplay`（四维评分：角色贴合度/场景礼仪/专业术语/应对能力）
- 新增 3 个内置场景 Prompt：interviewee（面试官）/ waiter（顾客）/ guide（游客）
- 新建 `backend/app/api/roleplay.py` + `backend/app/schemas/roleplay.py`，路由挂载到 `/api/roleplay`
- 前端 `frontend/src/api/roleplay.js` 封装接口调用
- `.env.example` 中 DEEPSEEK_API_KEY 替换为 BAILIAN_API_KEY
- `RolePlayView.vue` 大幅增强交互

### Commit 2 — feat: 淡紫可爱风 UI 改版 + 路由扁平化 + 文档
- 全局设计令牌从「Soft UI Evolution + Vibrant Education」改为「淡紫薰衣草可爱风」（品牌色 #A78BFA，Quicksand+Nunito 字体，马卡龙辅助色系）
- Favicon 更换为圆角方形 L 字母图标
- 路由扁平化：Introduction 合并进 TopNavLayout 根路径；/home 重定向到 /；/conversation 改为 TopNavLayout 子路由
- CLAUDE.md 同步更新技术栈与项目结构
- .gitignore 新增 `backend/edge_tts_output/`、`backend/test_*.wav`、`.~*` Office 锁文件
- 新增文档：`docs/8组-熊朝永-系统设计.docx`、`docs/图片/`（17 张设计图）
- 更新 `docs/需求说明书.docx`

**新增文件：**
- `backend/app/api/roleplay.py`
- `backend/app/schemas/roleplay.py`
- `frontend/src/api/roleplay.js`
- `docs/8组-熊朝永-系统设计.docx`
- `docs/图片/`

**修改文件：**
- `backend/app/services/llm.py` — 新增角色扮演方法
- `backend/main.py` — 注册 roleplay 路由
- `backend/.env.example` — deepseek → bailian
- `CLAUDE.md` — 技术栈/结构/模块状态更新
- `frontend/index.html` — 字体替换
- `frontend/public/favicon.svg` — 新图标
- `frontend/src/assets/styles/{tokens.css,variables.scss,element-override.scss,global.scss}` — 淡紫改版
- `frontend/src/components/layout/{AppLayout,SidebarNav,TopHeader,TopNavLayout}.vue`
- `frontend/src/router/index.js` — 路由扁平化
- `frontend/src/views/{admin/DashboardView,conversation/VoiceCallView,home/HomeView,introduction/IntroductionView,progress/ProgressView,roleplay/RolePlayView,teacher/StudentReportView}.vue`
- `.gitignore` — 排除生成产物与锁文件

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