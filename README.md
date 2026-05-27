# 🎙️ Lingolab-ai — 英语口语训练系统

> 基于 NLP 与大语言模型的英语口语训练系统，支持实时发音评测、个性化学习路径与沉浸式 AI 对话练习。

---

## 项目简介

Lingolab-ai 是一款面向全年龄段用户的智能英语口语训练平台，通过 AI 驱动的个性化教学、实时语音评估和情景对话模拟，为用户提供全天候的英语口语训练服务。

**核心能力：**

- 🎯 **智能水平测评** — AI 自适应测评，精准定位 CEFR 等级（A1-C2）
- 🔊 **发音评测与纠错** — 音素级五维评分，波形可视化展示发音问题
- 🤖 **AI 对话练习** — 60+ 真实场景沉浸式对话，AI 自动调整难度
- 📈 **个性化学习路径** — 基于用户画像定制每日学习任务
- 📊 **进度可视化追踪** — 雷达图、趋势曲线、能力热力图

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 · Vite · Pinia · Vue Router |
| 后端 | Python · FastAPI · SQLAlchemy |
| 数据库 | MySQL 8.0 |
| AI/NLP | DeepSeek· Whisper |
| 版本控制 | Git · GitHub |

---

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.11
- MySQL >= 8.0

### 1. 克隆仓库

```bash
git clone git@github.com:xiongchaoyong/Lingolab-ai.git
cd Lingolab-ai
```

### 2. 配置环境变量

```bash
# 后端
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入数据库连接信息和 API Key

# 前端
cp frontend/.env.example frontend/.env.local
# 编辑 frontend/.env.local，填入后端地址
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head        # 初始化数据库
uvicorn main:app --reload   # 启动开发服务器
# 访问 http://localhost:8000/docs 查看接口文档
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

---

## 项目结构

```
speakup/
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
│   │   ├── api/            # 路由层
│   │   ├── services/       # 业务逻辑层
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic Schema
│   │   └── core/           # 配置与工具
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt
│   └── main.py
├── docs/                   # 接口文档、架构说明
├── CLAUDE.md               # AI 协同开发规范
└── ai-log.md               # AI 操作日志
```

---

## 功能模块

| 模块 | 状态 |
|------|------|
| 用户注册与多维度画像 | 🚧 开发中 |
| 英语水平智能测评 | 🚧 开发中 |
| AI 发音评测与纠错 | 🚧 开发中 |
| 智能语音对话练习 | 🚧 开发中 |
| 个性化学习路径规划 | 📅 计划中 |
| 学习进度可视化追踪 | 📅 计划中 |
| 流利度与完整性评估 | 📅 计划中 |
| AI 语法纠错与润色 | 📅 计划中 |
| 情景角色扮演 | 📅 计划中 |
| 教师端教学管理后台 | 📅 计划中 |
| 运营管理后台 | 📅 计划中 |
| 游戏化闯关学习 | 🔮 后续迭代 |
| 学习社区与社交互动 | 🔮 后续迭代 |
| 智能客服系统 | 🔮 后续迭代 |

---

## 开发规范

本项目使用 Claude Code 进行 AI 辅助开发，协同规范详见 [CLAUDE.md](./CLAUDE.md)。

**分支规范：**

- `main` — 稳定版本，禁止直接 push
- `dev` — 日常集成分支
- `feat/功能名` — 功能开发分支

**提交规范：**

```
feat: 添加发音评测接口
fix: 修复登录 token 过期问题
docs: 更新接口文档
```

---

## 贡献

1. Fork 本仓库
2. 创建功能分支 `git checkout -b feat/your-feature`
3. 提交改动并发起 Pull Request
4. 等待 Code Review 通过后合入

---

## License

MIT
