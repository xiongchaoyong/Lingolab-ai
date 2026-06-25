# CLAUDE.md — 英语口语训练系统

> 本文件是团队与 Claude Code 的共同契约，所有成员共用，提交至 git 版本控制。
> Claude 犯错被纠正后，立即将教训追加至本文件末尾的「经验教训」章节。

---

## ⚠️ 编码前必读

**在进行任何代码编写前，必须先读取 `docs/ai-collaboration-standards.md`**，严格遵循其中的项目结构、前端/后端模式、命名规范和协作流程。所有 AI 生成的代码必须符合该规范。

**⛔ 开始编码前必须执行 Git 工作流（见下方「Git 工作流」章节），禁止在 main 分支上直接开发。**

---

## 项目概述

基于 NLP 与大语言模型的英语口语训练系统，覆盖全年龄段用户，支持发音评测、AI 智能对话、个性化学习路径等 **7 大服务模块、16 项子功能**（详见 `docs/需求说明书.docx`）。

- **行业**：在线教育 / 语言学习 / AI 教育
- **团队规模**：3人
- **小组成员**：XCY / PL / DJQ（**当前成员**）
- **交付周期**：1-2 个月

---

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3.5 + Vite 8 + Pinia 3 + Vue Router 4 | Node >= 18 |
| 后端 | Python + FastAPI + Uvicorn | Python >= 3.11 |
| 数据库 | MySQL 8+ + SQLAlchemy + Alembic | pymysql |
| 认证 | python-jose(JWT) + passlib(bcrypt) | 待对接 |
| **LLM** | **阿里百炼 DashScope（qwen-plus）** | 对话生成 / 语法纠错 / 翻译 / 评分 |
| ASR | WhisperX（small, int8） | 语音转文字 + 词级时间戳 |
| 发音评测 | wav2vec2 + GOP + CTC 强制对齐 | 五维评分（音素/重音/连读/语调/节奏） |
| TTS | Edge TTS（微软，免费） | 4 种音色，SSML 控速，句级时间戳 |
| 音频处理 | librosa + soundfile + pydub + ffmpeg | 特征提取 / 转码 |
| G2P | g2p-en | 音素→音标映射 |
| ML 框架 | PyTorch（Apple Silicon MPS 加速） | torch + torchaudio |

---

## 项目结构

```
/
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # Axios 封装（auth/pronunciation/conversation）
│   │   ├── assets/styles/       # CSS 变量 + SCSS + Element Plus 覆盖
│   │   ├── components/          # 通用（common/）+ 布局（layout/）+ 发音（pronunciation/）
│   │   ├── router/              # 路由配置 + 导航守卫（guest/auth/role）
│   │   ├── stores/              # Pinia（app/auth/assessment）
│   │   └── views/               # 18 个页面（admin/assessment/auth/community/conversation/...）
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/                 # 路由（conversation/pronunciation）
│   │   ├── services/            # 业务（asr/tts/llm/pronunciation）
│   │   ├── models/              # 仅 TimestampMixin，无具体表模型
│   │   ├── schemas/             # Pydantic（conversation/pronunciation/roleplay）
│   │   └── core/                # 配置 config.py + database.py
│   ├── requirements.txt
│   └── main.py                  # FastAPI 入口 + 路由注册 + 模型预加载
├── docs/                        # 文档
│   ├── prds/                    # PRD v1.0、v1.2、model-architecture-v1.1
│   ├── diagrams/                # .drawio + .png 架构图
│   ├── introduction.md          # 16 模块介绍
│   ├── TODO.md                  # 全部待办事项（按模块分组 + 优先级）
│   ├── ai-collaboration-standards.md  # AI 协作开发规范（前端/后端/工作流/提示词模板）
│   └── 功能模块需求分析/         # 模块分析工作流产出
├── CLAUDE.md
└── ai-log.md
```

---

## 常用命令

### 前端
```bash
cd frontend
npm install          # 安装依赖
npm run dev          # 开发服务器（默认 localhost:5173）
npm run build        # 生产构建
```

### 后端
```bash
cd backend
pip install -r requirements.txt          # 安装依赖
uvicorn main:app --reload                # 开发服务器（默认 localhost:8000）
```

### 数据库
```bash
mysql -u root -p
# 开发库：english_training_dev（Alembic 尚未初始化，通过 SQLAlchemy + init.sql 管理表结构）
```

---

## 7 大功能模块概述

> 对应 `docs/需求说明书.docx` 的模块划分。每模块包含若干子功能，共 16 项。

### 模块一：用户服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 1.1 | 用户注册 | ✅ 已实现 | 用户名+密码注册，bcrypt 加密，年龄自动归类 |
| 1.2 | 登录与鉴权 | ✅ 已实现 | JWT 24h 有效期，路由守卫（未测评→强制跳转） |
| 1.3 | 用户画像管理 | ✅ 已实现 | 多维度画像（年龄组/学习目标/兴趣/CEFR），乐观锁更新 |
| 1.4 | 英语水平智能测评 | ✅ 已实现 | ASR+LLM 自适应测评，30题种子数据，CEFR A1-C2 定级 |
| 1.5 | 学习路径生成 | ✅ 已实现 | 规则引擎六步法，测评后立即生成首次任务 |

### 模块二：学习服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 2.1 | AI 发音评测与纠错 | ✅ 已实现 | wav2vec2 + GOP 五维加权评分，33音素纠音词典 |
| 2.2 | 智能语音对话练习 | ✅ 已实现 | ASR→LLM→TTS 完整管线，SSE 流式，10轮上下文 |
| 2.3 | 流利度与完整性评估 | ⏳ 部分 | 已集成在对话评分中 |
| 2.4 | AI 语法纠错与润色 | ⏳ 部分 | 对话评分中已集成 LLM 文本评测 |
| 2.5 | 情景角色扮演 | ⏳ 部分 | 路由已挂载 + Schema 已定义，前端骨架页面 |

### 模块三：个性化推荐服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 3.1 | 个性化学习路径规划 | ✅ 已实现 | 知识图谱（128节点）+ 推荐算法，每日任务生成 |
| 3.2 | 学习资料智能推荐 | ✅ 已实现 | 三因子推荐（短板40%+难度35%+兴趣25%），视频/文章/音频 |

### 模块四：激励服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 4.1 | 游戏化闯关学习 | ✅ 已实现 | 每日闯关(5级递增难度)+配音挑战+积分(7种动作)+勋章(7种)，前端完整页面 |
| 4.2 | 学习进度可视化追踪 | ✅ 已实现 | 雷达图+趋势折线图+日历热力图+6项统计卡片，日/周/月/全部时间切换 |
| 4.3 | 学习效果预测与预警 | ✅ 已实现 | 线性回归预测达标日期+3条预警规则(不活跃/时长下降/发音停滞)+通知中心 |

### 模块五：社区服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 5.1 | 语音挑战广场 | ❌ 未开始 | - |
| 5.2 | 话题讨论区 | ❌ 未开始 | - |
| 5.3 | 学习小组 | ❌ 未开始 | - |

### 模块六：后台管理服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 6.1 | 教师端班级管理 | ❌ 未开始 | 前端骨架页面 |
| 6.2 | 学生报告与作业布置 | ❌ 未开始 | - |
| 6.3 | 运营端用户与内容管理 | ❌ 未开始 | 前端骨架页面 |
| 6.4 | 数据仪表盘 | ❌ 未开始 | - |

### 模块七：智能客服服务模块

| # | 子功能 | 实现状态 | 说明 |
|---|--------|----------|------|
| 7.1 | FAQ 自动应答 | ❌ 未开始 | - |
| 7.2 | 智能问题分类与转人工 | ❌ 未开始 | - |

---

## 代码规范

### 通用
- 代码注释使用中文，变量命名统一使用**英文**
- 提交信息统一格式：`type: 描述`（如 `feat: 添加发音接口`）
- Commit 类型：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`

### 前端（Vue 3）
- 组件名 PascalCase，文件名 kebab-case
- 使用 Composition API（`<script setup>`），不使用 Options API
- CSS 使用 scoped（除 `global.scss`）
- 接口请求统一封装在 `src/api/`，不在组件中直接调 axios

### 后端（Python + FastAPI）
- 变量/函数 snake_case，类名 PascalCase
- 路由按模块拆分在 `app/api/`，业务逻辑在 `services/`
- 所有接口必须有 Pydantic Schema 做请求/响应验证
- 错误处理统一用 `HTTPException`，不吞错误

### 数据库
- 表名用复数 snake_case，必须含 `id`（PK）、`created_at`、`updated_at`
- **迁移文件必须人工审查后才能执行，不得让 AI 自主运行 `alembic upgrade`**

---

## 禁止事项

- ❌ 禁止将 `.env` 文件提交至 git（使用 `.env.example` 替代）
- ❌ 禁止 AI 自主执行数据库迁移（`alembic upgrade`）
- ❌ 禁止在代码中硬编码 API Key、密码等敏感信息
- ❌ 禁止在前端组件中直接写业务逻辑，必须通过 store 或 api 层
- ❌ 禁止在 `main` 分支上直接编写代码，必须创建 `feat/` 分支

---

## 环境变量

后端 `backend/.env`（参考 `.env.example`）：

```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/english_training_dev
BAILIAN_API_KEY=                    # 阿里百炼 DashScope（替代 DeepSeek）
JWT_SECRET_KEY=change-me-to-a-random-string
HF_ENDPOINT=https://hf-mirror.com   # HuggingFace 国内镜像
DOUBAO_APP_ID=                      # 可选，豆包 TTS
DOUBAO_ACCESS_KEY=                  # 可选，豆包 TTS
```

前端 `frontend/.env.local`：

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Git 工作流

**每次开发前（Claude 自动执行，无需人工提醒）：**
1. `git checkout dev && git pull origin dev && git pull origin main`
2. `git checkout -b feat/功能名`
3. 分支命名：`feat/` / `fix/` / `refactor/` / `docs/`

**开发与提交：**
- 小粒度提交，每次只做一件事
- PR 合入 `dev`，至少 1 人 review
- PR 描述说明：做了什么、验证了什么、AI 生成部分是否已通读
- 每次 PR 同步更新 `ai-log.md`

**仓库：** git@github.com:xiongchaoyong/Lingolab-ai.git

---

## 自定义技能

| 技能名称 | 用途 |
|----------|------|
| `requirements-clarity` | 需求澄清（100 分评分系统→可执行 PRD） |
| `prompt-polish` | 提示词优化 |
| `drawio-skill` | 自然语言生成 draw.io 图表 |
| `module-analysis` | PRD 模块拆解→用例图→规格→流程图 |
| **`ui-ux-pro-max`** | **UI/UX 设计智能（67 样式/96 调色板/57 字体/13 框架）** |

---

## Claude Code 使用规范

- 每次任务先出计划，确认方案后再执行
- 开始新需求前自动执行：checkout dev → pull dev → pull main → 创建 feat 分支
- 任务粒度要小，一次只完成一个功能点
- 涉及数据库、鉴权、支付等高危模块，必须人工主导
- Claude 犯错被纠正后，立即将教训写入下方「经验教训」
- 每次编码完成后，Claude 必须做三件事：① 在对话中总结做了什么；② 将总结追加写入 `ai-log.md`；③ **先更新 ai-log.md → 再 commit**

---

## 经验教训

> `- [日期] 问题描述 → 正确做法`

- [2026-05-25] 项目初始化 push 后未同步更新 ai-log.md → 每次 git 操作必须同步更新 ai-log.md 记录操作摘要
- [2026-05-25] 先推送再补 log 导致反复遗漏 → 执行顺序：先更新 ai-log.md → 再 commit → 最后 push，确保 log 和变更在同一个 commit 里
- [2026-06-25] 在 main 分支上直接创建了新文件开始编码 → 开始任何编码任务前，必须先执行 Git 工作流：checkout dev → pull dev → pull main → 创建 feat/ 分支，编码前用 `git branch` 确认当前分支不是 main
