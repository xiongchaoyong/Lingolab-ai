# Lingolab-ai 项目全流程计划

> 创建时间：2026-05-28 | 作者：XCY | 当前阶段：需求分析完成，准备数据库设计

---

## 一、项目总览

| 项目 | 说明 |
|------|------|
| 名称 | Lingolab-ai — 英语口语训练系统 |
| 技术栈 | Vue 3 + FastAPI + MySQL 8.0 + Deepseek + Whisper |
| 团队 | 1 人（XCY） |
| 交付周期 | 8 周（Phase 1-3） |
| 仓库 | github.com/xiongchaoyong/Lingolab-ai |

### 全流程进度

```
环境准备   需求分析     设计阶段        开发阶段           测试交付
  ✅         ✅          ⬜             ⬜                 ⬜

Week 0    Week 0.5     Week 0.5-1    Week 1-6          Week 7-8
```

---

## 二、已完成（Phase 0：项目启动）

| 序号 | 任务 | 状态 | 产出 |
|:---:|------|:---:|------|
| 0.1 | 项目仓库初始化 | ✅ | Git 仓库 + README + .gitignore |
| 0.2 | 技术栈选型确认 | ✅ | Python FastAPI 确认，放弃 Java |
| 0.3 | CLAUDE.md 团队契约 | ✅ | 项目规范、Git 工作流、禁止事项 |
| 0.4 | Skills 技能配置 | ✅ | 5 个技能：product-manager / prompt-polish / drawio-skill / ui-ux-pro-max / simplify |
| 0.5 | Git 工作流规范 | ✅ | checkout dev → pull dev → pull main → 创建 feat 分支 |
| 0.6 | 项目文档初始化 | ✅ | introduction.md 项目介绍文档 |
| 0.7 | 需求分析（PRD） | ✅ | 16 模块完整 PRD + 系统架构图 + 模块依赖图 |

### 产出一览

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 团队契约 + 工作流规范 |
| `introduction.md` | 项目介绍（行业/功能/难点） |
| `docs/prds/lingolab-ai-v1.0-prd.md` | 完整产品需求文档（16 模块） |
| `docs/diagrams/drawio/system-boundary.drawio` | 系统边界图源文件 |
| `docs/diagrams/drawio/module-dependencies.drawio` | 模块依赖图源文件 |
| `docs/diagrams/png/system-boundary.png` | 系统边界图 |
| `docs/diagrams/png/module-dependencies.png` | 模块依赖图 |

---

## 三、进行中（Phase 1：设计阶段）

### Step 1：数据库设计

**目标**：根据 PRD 各模块数据结构，输出 ER 图 + DDL SQL

**核心表（预估 10-12 张）**：

| 表名 | 对应模块 | 说明 |
|------|:---:|------|
| user_profiles | 模块 1 | 用户画像，年龄/等级/目标/兴趣 |
| assessment_records | 模块 2 | 测评记录，CEFR + 四维分数 |
| assessment_questions | 模块 2 | 测评题库，难度+维度+答案 |
| pronunciation_records | 模块 4 | 发音记录，五维分数+错误音素 |
| conversation_sessions | 模块 6 | 对话会话，场景+难度+状态 |
| conversation_messages | 模块 5/6/7 | 消息+流利度+语法纠错 |
| daily_tasks | 模块 3 | 每日任务，内容+完成状态 |
| learning_materials | 模块 9 | 推荐资料库，视频/文章/音频 |
| material_records | 模块 9 | 用户学习资料记录 |
| notices | 模块 13 | 通知/预警/勋章 |
| classes | 模块 14 | 班级（教师端） |
| class_members | 模块 14 | 班级成员 |
| assignments | 模块 14 | 作业布置+提交 |

**交付物**：
- [ ] ER 图（draw.io）
- [ ] DDL SQL 文件
- [ ] Alembic 初始化迁移

### Step 2：API 接口设计

**目标**：定义 Phase 1（P0 模块）REST API 端点

**预估接口数**：20-25 个

| 模块 | 预估接口 | 主要端点 |
|------|:---:|------|
| 模块 1 画像 | 3 | POST /auth/register, POST /auth/login, GET /auth/me |
| 模块 2 测评 | 4 | GET /assessment/start, POST /assessment/answer, GET /assessment/report |
| 模块 4 发音 | 4 | GET /pronounce/content, POST /pronounce/evaluate, GET /pronounce/history |
| 模块 6 对话 | 5 | GET /converse/scenarios, POST /converse/start, POST /converse/message, GET /converse/report |

**交付物**：
- [ ] API 接口文档（按模块分）
- [ ] 请求/响应 Schema 定义
- [ ] 错误码规范

### Step 3：项目脚手架搭建

**目标**：初始化前后端项目骨架，跑通联调

**前端**：
- [ ] Vite + Vue 3 + TypeScript 初始化
- [ ] Pinia + Vue Router 配置
- [ ] API 请求封装（Axios）
- [ ] 基础布局组件 + 路由结构

**后端**：
- [ ] FastAPI 项目结构初始化
- [ ] SQLAlchemy 2.0 + Alembic 配置
- [ ] JWT 鉴权中间件
- [ ] 统一错误处理 + 响应格式
- [ ] CORS 配置

**交付物**：
- [ ] 前后端联调成功（GET /api/health → 200）

---

## 四、待开始（Phase 2：开发阶段）

### Phase 2.1 — 核心 MVP（第 1-4 周）

| Sprint | 模块 | 任务拆解 | 预估 |
|:---:|------|------|:---:|
| Sprint 1 | 模块 1 画像 | 注册接口 → 登录接口 → JWT 鉴权 → 画像 CRUD | 3 天 |
| Sprint 2 | 模块 2 测评 | 题库管理 → 自适应引擎 → 测评报告 → 强制测评逻辑 | 5 天 |
| Sprint 3 | 模块 4 发音 | 内容库 → Whisper 集成 → 五维评分 → 结果展示页 | 5 天 |
| Sprint 4 | 模块 6 对话 | 场景管理 → Deepseek 集成 → TTS 集成 → 对话页面 | 7 天 |

**里程碑**：用户可注册 → 测评 → 跟读 → AI 对话，完整走通核心闭环

### Phase 2.2 — 学习闭环（第 5-6 周）

| Sprint | 模块 | 任务拆解 | 预估 |
|:---:|------|------|:---:|
| Sprint 5 | 模块 3+5 | 路径生成引擎 + 每日任务 + 流利度嵌入对话 | 5 天 |
| Sprint 6 | 模块 7+9 | 语法纠错嵌入 + 资料推荐引擎 | 3 天 |
| Sprint 7 | 模块 12 | 进度页（雷达图/折线图/热力图）+ 学习统计 | 4 天 |

**里程碑**：用户有完整学习闭环（路径→练习→纠错→推荐→看进度）

### Phase 2.3 — 激励留存（第 7-8 周）

| Sprint | 模块 | 任务拆解 | 预估 |
|:---:|------|------|:---:|
| Sprint 8 | 模块 8+10 | 角色扮演 + 每日闯关 + 配音挑战 + 积分勋章 | 5 天 |
| Sprint 9 | 模块 13 | 线性回归预测 + 3 条预警规则 + 通知系统 | 3 天 |
| Sprint 10 | 模块 14+15 | 教师班级管理 + 运营数据看板 + 内容管理 | 4 天 |

**里程碑**：用户留存体系上线，教师和运营可管理

### Phase 2.4 — 平台化（后续迭代）

| Sprint | 模块 | 任务拆解 |
|:---:|------|------|
| Sprint 11 | 模块 11 | 语音挑战 + 话题讨论 + 学习小组 |
| Sprint 12 | 模块 16 | 智能客服 + FAQ |

---

## 五、测试与交付（第 8 周+）

### 测试计划

| 类型 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 后端 Service 层 ≥ 60% 覆盖 | pytest |
| 接口测试 | P0 模块全部 API | httpx / Postman |
| 端到端测试 | 注册→测评→发音→对话完整链路 | 手动 |
| 性能测试 | 对话接口并发 50 QPS | Locust |
| 兼容性测试 | Chrome/Safari/Edge, 375/768/1440px | 手动 |

### 验收清单

- [ ] Phase 1 4 个 P0 模块功能完整
- [ ] 对话端到端延迟 < 3s
- [ ] 发音评分五维正常返回
- [ ] 无硬编码密钥，所有敏感信息走环境变量
- [ ] 数据库 migration 通过人工审查
- [ ] 前端 Lighthouse ≥ 85
- [ ] 响应式适配 375/768/1440

### 部署计划

| 环境 | 方式 | 说明 |
|------|------|------|
| 开发环境 | 本地 localhost | FastAPI + Vite dev server |
| 测试环境 | 待定 | 阿里云/腾讯云 低配 ECS |
| 生产环境 | 待定 | 至少 2C4G + SSL + 域名 |

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|:---:|:---:|------|
| 1 人开发进度不足 | 高 | 延期 | P1/P2 按模块独立，可随时裁剪 |
| Whisper 延迟 > 预期 | 中 | 体验差 | 异步评分 + 前端先展示转写 |
| Deepseek 服务不稳定 | 中 | 对话中断 | 超时降级 + 预设回复 + 重试 |
| 多年龄发音识别差 | 中 | 评测不准 | 聚焦 15-40 岁，其余用宽松阈值 |
| 首次接触 Vue3/FastAPI | 低 | 学习成本 | 脚手架阶段预留学习缓冲 |

---

## 七、文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 团队契约 | `CLAUDE.md` | 规范/工作流/经验教训 |
| 项目介绍 | `introduction.md` | 行业/功能/难点 |
| 需求 PRD | `docs/prds/lingolab-ai-v1.0-prd.md` | 16 模块完整需求 |
| 项目计划 | `docs/project-plan.md` | 本文档 |
| 操作日志 | `ai-log.md` | AI 辅助操作记录 |
| 系统边界图 | `docs/diagrams/png/system-boundary.png` | 系统架构 |
| 模块依赖图 | `docs/diagrams/png/module-dependencies.png` | 16 模块依赖 |
