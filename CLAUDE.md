# CLAUDE.md — 英语口语训练系统

> 本文件是团队与 Claude Code 的共同契约，所有成员共用，提交至 git 版本控制。
> Claude 犯错被纠正后，立即将教训追加至本文件末尾的「经验教训」章节。

---

## 项目概述

基于 NLP 与大语言模型的英语口语训练系统，支持发音评测、AI 对话练习、个性化学习路径等功能。

- **行业**：在线教育 / 语言学习 / AI 教育
- **团队规模**：3人
- **小组成员:XCY  PL   DJQ**   
- **当前成员:DJQ**   **
- **交付周期**：1-2 个月

---

## 技术栈

| 层次 | 技术 | 版本要求 |
|------|------|----------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router | Node.js >= 18 |
| 后端 | Python + FastAPI | Python >= 3.11 |
| 数据库 | MySQL | >= 8.0 |
| ORM | SQLAlchemy + Alembic | 最新稳定版 |
| AI/NLP | Deepseek | 按需接入 |
| 语音处理 | Whisper API（后端转写） | - |
| 包管理 | 前端 npm，后端 pip + requirements.txt | - |

---

## 项目结构(后期可修改)

```
/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # 接口请求封装
│   │   └── router/         # 路由配置
│   └── vite.config.js
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由层（按模块拆分）
│   │   ├── services/       # 业务逻辑层
│   │   ├── models/         # 数据库模型（SQLAlchemy）
│   │   ├── schemas/        # 请求/响应 Schema（Pydantic）
│   │   └── core/           # 配置、依赖注入、工具函数
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt
│   └── main.py
├── docs/                   # 接口文档、架构说明
├── CLAUDE.md               # 本文件
└── ai-log.md               # AI 操作日志
```

---

## 常用命令

### 前端
```bash
cd frontend
npm install          # 安装依赖
npm run dev          # 启动开发服务器（默认 http://localhost:5173）
npm run build        # 生产构建
npm run lint         # 代码检查
```

### 后端
```bash
cd backend
pip install -r requirements.txt          # 安装依赖
uvicorn main:app --reload                # 启动开发服务器（默认 http://localhost:8000）
alembic upgrade head                     # 执行数据库迁移
alembic revision --autogenerate -m "描述" # 生成迁移文件（需人工审查后再执行）
```

### 数据库
```bash
mysql -u root -p                         # 连接数据库
# 数据库名：english_training_dev（开发）/ english_training_test（测试）
```

---

## 代码规范

### 通用
- 代码注释使用中文，变量命名统一使用**英文**
- 提交信息使用中文或英文均可，但格式统一：`feat: 添加发音接口`
- Commit 类型：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`

### 前端（Vue 3）
- 组件名使用 PascalCase，如 `VoiceRecorder.vue`
- 文件名使用 kebab-case，如 `voice-recorder.vue`
- 使用 Composition API（`<script setup>`），不使用 Options API
- CSS 使用 scoped，不写全局样式（除 `global.css`）
- 接口请求统一封装在 `src/api/` 下，不在组件中直接调用 axios

### 后端（Python + FastAPI）
- 变量和函数名使用 snake_case，类名使用 PascalCase
- 路由文件按模块拆分，放在 `app/api/` 下
- 业务逻辑放在 `services/`，路由层只做参数校验和调用 service
- 所有接口必须有 Pydantic Schema 做请求/响应验证
- 错误处理统一使用 FastAPI 的 `HTTPException`，不要 `try/except` 吞掉错误

### 数据库
- 表名使用复数 snake_case，如 `user_profiles`、`learning_records`
- 所有表必须有 `id`（主键）、`created_at`、`updated_at` 字段
- **数据库迁移文件必须人工审查后才能执行，不得让 AI 自主运行 `alembic upgrade`**

---

## 禁止事项

- ❌ 禁止将 `.env` 文件提交至 git（使用 `.env.example` 替代）
- ❌ 禁止 AI 自主执行数据库迁移（`alembic upgrade`）
- ❌ 禁止在代码中硬编码 API Key、密码等敏感信息
- ❌ 禁止在前端组件中直接写业务逻辑，必须通过 store 或 api 层

---

## 环境变量

后端在 `backend/.env` 中配置（参考 `backend/.env.example`）：

```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/english_training_dev
OPENAI_API_KEY=
CLAUDE_API_KEY=
JWT_SECRET_KEY=
WHISPER_API_KEY=
```

前端在 `frontend/.env.local` 中配置：

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Git 工作流

**每次开发前（Claude 自动执行，无需人工提醒）：**
1. 切换到 `dev` 分支：`git checkout dev`
2. 拉取最新代码：`git pull origin dev`
3. 基于最新 `dev` 创建功能分支：`git checkout -b feat/功能名`

**开发与提交：**
4. 小粒度提交，每次只做一件事
5. 完成后发 PR 合入 `dev`，至少 1 人 review
6. PR 描述必须说明：做了什么、验证了什么、AI 生成部分是否已通读
7. 每次 PR 同步更新 `ai-log.md`
8. `main` 分支只在里程碑节点从 `dev` 合入，打版本 tag

**分支命名规范：**
- 新功能：`feat/功能名`（如 `feat/voice-recorder`）
- 修复：`fix/问题描述`（如 `fix/login-error`）
- 重构：`refactor/模块名`
- 文档：`docs/内容描述`

**仓库地址：**git@github.com:xiongchaoyong/Lingolab-ai.git   或  https://github.com/xiongchaoyong/Lingolab-ai.git

---

## 自定义技能（Skills）

项目在 `.claude/skills/` 目录下存放自定义技能，Claude Code 会自动发现并加载，团队成员均可使用：

| 技能名称 | 文件 | 用途 |
|------|------|------|
| `product-manager` | `.claude/skills/product-manager/SKILL.md` | 需求澄清：通过 100 分评分系统将模糊需求转为可执行 PRD |
| `prompt-polish` | `.claude/skills/prompt-polish/SKILL.md` | 提示词优化：将粗糙提示词转为精准 AI 提示词 |

使用方式：在 Claude Code 中输入 `/product-manager` 或 `/prompt-polish` 调用。

---

## Claude Code 使用规范

- 每次任务先让 Claude 出计划，确认方案后再执行
- **开始任何新需求前，Claude 自动执行：checkout dev → pull → 创建 feat 分支，无需人工提醒**
- 任务粒度要小，一次只完成一个功能点
- 涉及数据库、鉴权、支付等高危模块，必须人工主导
- Claude 犯错被纠正后，立即将教训写入下方「经验教训」章节
- CLAUDE.md 控制在 200 行以内，子模块可在对应目录下建独立 CLAUDE.md

---

## 经验教训

> 在此追加 Claude 犯错后的纠正记录，格式如下：
> `- [日期] 问题描述 → 正确做法`

- [2026-05-25] 项目初始化 push 后未同步更新 ai-log.md → 每次 git 操作（push、PR 等）必须同步更新 ai-log.md 记录操作摘要
- [2026-05-25] 先推送再补 log 导致反复遗漏 → 执行顺序：先更新 ai-log.md → 再 commit → 最后 push，确保 log 和变更在同一个 commit 里
