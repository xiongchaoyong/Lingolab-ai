# 项目文件目录说明

> 本文档介绍 Lingolab-ai 项目的完整目录结构和每个文件/目录的用途。
> 最后更新：2026-05-28 | 项目阶段：规划期

---

## 目录总览

```
Lingolab-ai/
├── .gitignore                  # Git 忽略规则
├── .claude/                    # Claude Code 配置与技能
├── CLAUDE.md                   # 项目宪章（团队 + AI 共享）
├── README.md                   # 项目说明
├── ai-log.md                   # AI 操作日志
├── introduction.md             # 项目介绍与背景
├── demo/                       # 演示文件
└── docs/                       # 项目文档
    ├── prds/                   # 产品需求文档
    ├── diagrams/               # 架构图（drawio + png）
    └── *.md                    # 各类文档
```

---

## 一、项目根目录

| 文件/目录 | 用途 | 说明 |
|-----------|------|------|
| `.gitignore` | Git 忽略规则 | 定义哪些文件不提交到版本控制（如 `.env`、`node_modules` 等） |
| `CLAUDE.md` | 项目宪章 | 团队与 AI 的共同契约，包含技术栈、代码规范、Git 工作流、经验教训等 |
| `README.md` | 项目说明 | GitHub 仓库首页展示的项目简介 |
| `ai-log.md` | AI 操作日志 | 记录每次 AI 辅助的 git 操作摘要（commit、push、PR 等） |
| `introduction.md` | 项目背景介绍 | 项目定位、业务背景、目标用户等详细说明 |
| `demo/` | 演示文件目录 | 存放演示页面，目前包含 `index.html` |

---

## 二、.claude/ — Claude Code 配置目录

### 目录结构

```
.claude/
├── settings.json              # 团队级权限配置（提交 git）
├── settings.local.json        # 个人级权限配置（不提交 git）
└── skills/                    # 自定义技能
    ├── drawio-skill/          # AI 绘图技能
    ├── product-manager/       # 需求澄清技能
    ├── prompt-polish/         # 提示词优化技能
    └── ui-ux-pro-max/         # UI/UX 设计技能
```



---

## 三、docs/ — 项目文档

### 3.1 文档文件

| 文件 | 用途 |
|------|------|
| `claude-code-团队使用指南.md` | Claude Code 的配置说明和团队使用教程 |
| `project-plan.md` | 项目全流程计划文档 |

### 3.2 docs/prds/ — 产品需求文档

| 文件 | 用途 |
|------|------|
| `lingolab-ai-v1.0-prd.md` | 项目 v1.0 完整 PRD（含 16 个模块需求） |

### 3.3 docs/diagrams/ — 架构图

#### drawio/ — 可编辑源文件

| 文件 | 内容 |
|------|------|
| `lingolab-architecture.drawio` | 系统架构图 |
| `module-dependencies.drawio` | 模块依赖关系图 |
| `system-boundary.drawio` | 系统边界图 |
| `.$system-boundary.drawio.bkp` | 系统边界图备份文件（`$` 表示 Office 临时文件） |

#### png/ — 导出的图片

| 文件 | 内容 |
|------|------|
| `lingolab-architecture.png` | 系统架构图截图 |
| `module-dependencies.png` | 模块依赖关系图截图 |
| `system-boundary.png` | 系统边界图截图 |

---


