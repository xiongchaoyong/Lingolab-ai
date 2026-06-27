# Lingolab — AI 驱动的英语口语训练系统

> 基于 NLP 与大语言模型的智能英语口语训练平台，覆盖全年龄段用户，提供端到端语音交互、专业级发音评测与个性化学习路径。
>
> Speak smarter, not harder.

---

## 项目简介

Lingolab 是一款面向全年龄段用户的智能英语口语训练系统，通过 **ASR（WhisperX）→ LLM（千问）→ TTS（Edge TTS）** 端到端语音交互管线，结合 **wav2vec2 + GOP + CTC 强制对齐** 的专业级发音评测，为用户提供全天候、个性化的英语口语训练服务。

### 六大核心竞争力

| # | 能力 | 说明 |
|---|------|------|
| 1 | **端到端语音交互** | ASR → LLM → TTS 全链路本地完成，延迟可控，接近真人对话节奏 |
| 2 | **专业级发音评测** | wav2vec2 + GOP + CTC 强制对齐，音素级五维评分（音素/重音/连读/语调/节奏） |
| 3 | **AI 全链路个性化** | 测评定级 → 知识图谱路径规划 → 四因子推荐 → 效果预测，完整学习闭环 |
| 4 | **全年龄段覆盖** | 儿童到中老年，场景从日常交流到商务谈判，适用面广 |
| 5 | **技术先进成本可控** | LLM 用国产千问、TTS 用微软免费方案、ASR 和评测本地运行 |
| 6 | **完整教学管理生态** | 覆盖 C 端学习者 + 教师端 + 运营端，具备 B 端商业化潜力 |

---

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3.5 + Vite 8 + Pinia 3 + Vue Router 4 + Element Plus | Node >= 18 |
| 后端 | Python 3.11+ + FastAPI + Uvicorn + SQLAlchemy | 异步 RESTful API |
| 数据库 | MySQL 8.0 + Alembic | pymysql 驱动 |
| 认证 | python-jose (JWT) + passlib (bcrypt) | 24h Token 有效期 |
| **LLM** | **阿里百炼 DashScope（qwen-plus）** | 对话生成 / 语法纠错 / 翻译 / 评分 |
| **ASR** | **WhisperX（small, int8）** | 语音转文字 + 词级时间戳 |
| **发音评测** | **wav2vec2 + GOP + CTC 强制对齐** | 五维评分（音素/重音/连读/语调/节奏） |
| **TTS** | **Edge TTS（微软，免费）** | 4 种音色，SSML 控速，句级时间戳 |
| 音频处理 | librosa + soundfile + pydub + ffmpeg | 特征提取 / 转码 |
| ML 框架 | PyTorch（Apple Silicon MPS 加速） | torch + torchaudio |

---

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.11
- MySQL >= 8.0
- ffmpeg（音频转码）

### 1. 克隆仓库

```bash
git clone git@github.com:xiongchaoyong/Lingolab-ai.git
cd Lingolab-ai
```

### 2. 配置环境变量

**后端 `backend/.env`：**

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/english_training_dev
BAILIAN_API_KEY=                    # 阿里百炼 DashScope API Key
JWT_SECRET_KEY=change-me-to-a-random-string
HF_ENDPOINT=https://hf-mirror.com   # HuggingFace 国内镜像
```

**前端 `frontend/.env.local`：**

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# 访问 http://localhost:8000/docs 查看 Swagger 接口文档
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 5. 生成模拟数据（可选）

```bash
cd backend
python seed_all_modules.py           # 全模块模拟数据
python seed_leaderboard_teacher.py   # 排行榜 + 教师管理数据
```

---

## 项目结构

```
Lingolab-ai/
├── frontend/                          # Vue 3 前端
│   └── src/
│       ├── api/                       # Axios 封装（按模块拆分）
│       ├── assets/styles/             # CSS 变量 + SCSS + Element Plus 覆盖
│       ├── components/                # 通用组件（common/）+ 布局（layout/）
│       ├── router/                    # 路由 + 导航守卫（guest/auth/role）
│       ├── stores/                    # Pinia 状态管理（auth/admin/community/gamification）
│       └── views/                     # 页面视图（按功能模块分组）
│           ├── admin/                 # 运营管理后台
│           ├── assessment/            # 水平测评
│           ├── auth/                  # 登录/注册/个人资料
│           ├── community/             # 学习社区
│           ├── conversation/          # AI 智能对话
│           ├── gamification/          # 游戏化闯关
│           ├── introduction/          # 首页
│           ├── learning/              # 学习路径 + 进度追踪
│           ├── roleplay/              # 情景角色扮演
│           ├── student/               # 学生端（我的班级/作业）
│           └── teacher/               # 教师端（班级管理/作业/报告）
├── backend/                           # FastAPI 后端
│   ├── app/
│   │   ├── api/                       # 路由层（按模块拆分）
│   │   ├── services/                  # 业务逻辑层（ASR/TTS/LLM/发音/社区/管理）
│   │   ├── models/                    # SQLAlchemy ORM 模型
│   │   ├── schemas/                   # Pydantic 请求/响应 Schema
│   │   └── core/                      # 配置 / 数据库 / 安全（JWT）
│   ├── seed_all_modules.py            # 全模块模拟数据种子
│   ├── requirements.txt
│   └── main.py                        # FastAPI 入口 + 路由注册 + 模型预加载
├── docs/                              # 文档
│   ├── prds/                          # PRD 文档
│   ├── diagrams/                      # 架构图
│   ├── introduction.md                # 16 模块详细介绍
│   ├── ai-collaboration-standards.md  # AI 协作开发规范
│   └── 功能模块需求分析/              # 模块分析工作流产出
├── CLAUDE.md                          # AI 协同开发规范
└── ai-log.md                          # AI 操作日志
```

---

## 功能模块（16 个）

| # | 模块 | 状态 | 说明 |
|---|------|------|------|
| 1 | 用户注册与多维度画像 | ✅ 已实现 | JWT 注册/登录/个人资料/画像 |
| 2 | 英语水平智能测评 | ✅ 已实现 | 自适应难度 + CEFR 定级 + 口语 ASR 评分 |
| 3 | 个性化学习路径规划 | ✅ 已实现 | 知识图谱 + NetworkX BFS/拓扑排序 |
| 4 | AI 发音评测与纠错 | ✅ 已实现 | wav2vec2 + GOP 五维加权评分 |
| 5 | 流利度与完整性评估 | ✅ 已实现 | 集成在对话评分中（语速/停顿/重复/语法/相关性） |
| 6 | 智能语音对话练习 | ✅ 已实现 | ASR→LLM→TTS 完整管线，SSE 流式，8 个场景 |
| 7 | AI 语法纠错与润色 | ✅ 已实现 | LLM 语法纠错 + 润色建议 + 语音输入 |
| 8 | 情景角色扮演 | ✅ 已实现 | 8 个角色 + 四维评分 |
| 9 | 学习资料智能推荐 | ✅ 已实现 | 知识图谱四因子评分推荐 |
| 10 | 游戏化闯关学习 | ✅ 已实现 | 每日闯关 + 配音挑战 + 积分 + 勋章 |
| 11 | 学习社区与社交互动 | ✅ 已实现 | 语音挑战广场 + 讨论区 + 学习小组 |
| 12 | 学习进度可视化追踪 | ✅ 已实现 | 雷达图 + 趋势折线图 + 日历热力图 |
| 13 | 学习效果预测与预警 | ✅ 已实现 | 线性回归预测 + 3 条预警规则 |
| 14 | 教师端教学管理后台 | ✅ 已实现 | 班级管理 + 作业布置 + 提交点评 |
| 15 | 运营管理后台 | ✅ 已实现 | 用户管理 + 数据仪表盘 + 操作日志 |
| 16 | 智能客服与帮助系统 | ✅ 已实现 | LLM 智能问答 + 问题分类 + 转人工 + 语音输入 |

---

## 开发规范

### Git 工作流

- `main` — 稳定版本，禁止直接 push
- `dev` — 日常集成分支
- `feat/功能名` — 功能开发分支
- `fix/问题名` — Bug 修复分支

### 提交规范

```
feat: 添加发音评测接口
fix: 修复登录 token 过期问题
docs: 更新接口文档
refactor: 重构对话服务
test: 添加发音模块测试
chore: 更新依赖
```

### 代码规范

- 前端：Composition API（`<script setup>`），组件 PascalCase，文件名 kebab-case
- 后端：变量 snake_case，类 PascalCase，路由按模块拆分
- 数据库：表名复数 snake_case，必须含 `id`、`created_at`、`updated_at`
- 所有接口必须有 Pydantic Schema 做请求/响应验证

### 禁止事项

- 禁止提交 `.env` 文件至 git
- 禁止 AI 自主执行数据库迁移（`alembic upgrade`）
- 禁止在代码中硬编码 API Key、密码等敏感信息
- 禁止在 `main` 分支上直接编写代码

详见 [CLAUDE.md](./CLAUDE.md) 和 [AI 协作开发规范](./docs/ai-collaboration-standards.md)。

---

## 团队

| 成员 | 角色 |
|------|------|
| XCY | 全栈开发 |
| PL | 后端开发 |
| DJQ | 前端开发 |

---

## License

MIT