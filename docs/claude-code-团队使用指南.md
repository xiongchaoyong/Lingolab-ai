# Claude Code 团队使用指南

> 本文档面向 Lingolab-ai 项目全体成员，介绍 Claude Code 的配置、功能和使用方法。
> 最后更新：2026-05-28 | Claude Code 版本：2.1.89

---

## 一、什么是 Claude Code？

Claude Code 是 Anthropic 推出的**命令行 AI 编程助手**，运行在终端中，能直接读写你的代码、执行命令、操作 git。它不是浏览器里的聊天机器人——它直接在你的项目目录里工作，理解整个代码库的上下文。

**能做什么：**
- 根据需求直接写代码、改代码
- 自动执行 git 分支管理、提交、发 PR
- 阅读和理解整个项目结构
- 运行测试、调试错误
- 通过「技能」扩展专业能力（画图、需求澄清、UI 设计等）

**不能做什么：**
- 替代你做的架构决策——最终决定权在你
- 自主执行数据库迁移（项目已禁止）
- 访问你未授权的文件或网络

---

## 二、安装与启动

### 2.1 安装

```bash
# 需要 Node.js >= 18
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

### 2.2 启动

```bash
# 进入项目目录后直接启动
cd /path/to/Lingolab-ai
claude

# 或带初始提示启动
claude "帮我实现登录功能"
```

首次使用需要绑定 Anthropic API Key（联系项目负责人获取）。

---

## 三、当前项目配置总览

```
Lingolab-ai/
├── CLAUDE.md                    ← 项目宪章（团队共享，已提交 git）
├── .claude/
│   ├── settings.json            ← 团队级权限配置（已提交 git）
│   ├── settings.local.json      ← 个人级权限配置（不提交 git）
│   └── skills/                  ← 自定义技能目录
│       ├── product-manager/     ← 需求澄清技能
│       ├── prompt-polish/       ← 提示词优化技能
│       ├── drawio-skill/        ← AI 绘图技能
│       └── ui-ux-pro-max/       ← UI/UX 设计技能
```

---



## 四、CLAUDE.md — 项目宪章

### 4.1 它是什么？

`CLAUDE.md` 是项目根目录下的一个 Markdown 文件，它是**团队与 AI 之间的共同契约**。每次 Claude Code 启动时都会自动读取这个文件，并严格按照其中的规则来工作。

### 4.2 为什么要放在根目录而不是 .claude 里？

Claude Code 支持三个层级的 CLAUDE.md，各有不同用途：

| 位置 | 用途 | 是否提交 git | 谁可见 |
|------|------|-------------|--------|
| `~/.claude/CLAUDE.md` | 你个人的全局偏好，跨所有项目生效 | ❌ | 仅自己 |
| `.claude/CLAUDE.md` | 你在这个项目里的个人偏好 | ❌ | 仅自己 |
| `CLAUDE.md`（根目录）| 团队共享的项目规范 | ✅ | **所有人** |

根目录的 `CLAUDE.md` 是团队宪章，放在最显眼的位置，GitHub 上直接可见，方便新成员快速了解项目规范。

### 4.3 当前 CLAUDE.md 包含什么？

| 章节 | 内容 |
|------|------|
| 项目概述 | 项目定位、团队规模、交付周期 |
| 技术栈 | 前端 Vue3、后端 FastAPI、数据库 MySQL 等完整技术选型 |
| 项目结构 | 前后端目录组织规范 |
| 常用命令 | 前端/后端/数据库的开发命令 |
| 代码规范 | 命名规范、文件组织、前后端编码标准 |
| 禁止事项 | 不能提交 .env、不能 AI 自主跑数据库迁移等 |
| Git 工作流 | 分支命名规范、开发流程、PR 要求 |
| 自定义技能 | 项目中可用的 Skills 列表 |
| Claude Code 使用规范 | 任务粒度、审核要求等 |
| 经验教训 | Claude 犯错的纠正记录 |

### 4.4 如何使用 CLAUDE.md？

当你使用 Claude Code 时，不需要手动告诉它项目规范——它会自动读取 CLAUDE.md 并遵守其中的规则。例如：

- **Git 工作流**：你说「开始开发登录功能」，Claude 会自动执行 `checkout dev → pull dev → pull main → 创建 feat/xxx 分支`
- **代码规范**：Claude 会自动用 Composition API 写 Vue 组件，用 snake_case 写 Python 函数
- **禁止事项**：Claude 不会主动执行 `alembic upgrade`，不会硬编码密码

### 4.5 如何修改 CLAUDE.md？

直接在根目录编辑 `CLAUDE.md`，然后提交到 git。所有团队成员共享同一份宪章。

**Claude 被纠正后：** 立即把教训追加到文件末尾的「经验教训」章节，格式如下：

```
- [日期] 问题描述 → 正确做法
```

---







## 五、Skills — 自定义技能

技能是 Claude Code 的**专业扩展模块**，给 AI 注入特定领域的知识和能力。项目当前配置了 **4 个技能**：



**使用方式由两种:**

**1.你给的提示词中说明你需要的技能，比如"使用drawio画图skill帮我画一个登录注册的流程图"，calude code会自动识别**

2. **/drawio-skill  帮我画一个登录注册的流程图 ，如图**

**![image-20260528153123612](/Users/x/Library/Application Support/typora-user-images/image-20260528153123612.png)**

**（前面的/drawio-skill 是命令，指定claude code使用这个skill，在命令后面就可以接上你要的提示词） "**



### 5.1 product-manager — 需求澄清

**用途：** 当你有一个模糊的需求想法时，通过 100 分评分系统和针对性提问，将其转化为可执行的 PRD。

**什么时候用：**

- 需求描述不清晰（如「加个登录功能」——用什么方式登录？OAuth？手机号？）
- 功能复杂，预计超过 2 天工作量
- 涉及跨模块协作

**怎么用：**

```
 /product-manager 用户需要一个打卡功能  （其中的 / 用于选择对应的命令）
```

### 5.2 prompt-polish — 提示词优化

**用途：** 将粗糙的 AI 提示词优化为精准、高效的版本。适合写 AI 对话提示词、系统 prompt 等。

**怎么用：**
```
 /prompt-polish 让AI帮学生纠正发音错误
```

### 5.3 drawio-skill — AI 绘图

注意⚠️:需要下载drawio桌面版，下载链接https://github.com/jgraph/drawio-desktop/releases

<img src="/Users/x/Library/Application Support/typora-user-images/image-20260528153319451.png" alt="image-20260528153319451" style="zoom:50%;" />





**用途：** 用自然语言描述，自动生成 draw.io 图表。支持：

- 流程图
- 系统架构图
- ER 图 / UML 类图
- 时序图
- 神经网络模型图
- 思维导图

**怎么用：**
```
/drawio-skill 画一个用户注册到登录的完整流程图
```

生成的 `.drawio` 文件可以用 draw.io 桌面版或在线版打开编辑。



**最后会生成两个文件:一个是png图片，还有一个是.drawio文件，可以用draw.io 打开手动修改流程图**



### 5.4 ui-ux-pro-max — UI/UX 设计

**用途：** UI/UX 设计智能助手，内置 67 种设计风格、96 套配色方案、57 种字体搭配、25 种图表类型。支持 React、Vue、Tailwind、shadcn/ui 等 13 种技术栈。

**什么时候用：**
- 设计新页面或组件
- 选择配色方案和字体搭配
- 审查和改进现有 UI

**怎么用：**
```
/ui-ux-pro-max 设计一个学习进度仪表盘页面
```

---





## 六、日常使用场景

### 场景 1：开发新功能

```
# 直接告诉 Claude 需求
claude "实现发音评测接口，接收音频文件返回评分和错误位置"

# Claude 会自动：
# 1. 按 CLAUDE.md 规范创建分支
# 2. 出方案让你确认
# 3. 写后端 service + route + schema
# 4. 写前端页面和 API 封装
# 5. 小粒度提交
```

### 场景 2：审查和修改代码

```
# 在 Claude Code 交互中说：
"帮我 review 一下 app/services/speech_service.py，看看有没有性能问题"
"把这个组件从 Options API 改成 Composition API"
"给所有 API 路由加上统一的错误处理"
```

### 场景 3：写文档和画图

```
/drawio-skill 画一个系统架构图，包含前端、后端、数据库、AI服务
"帮我生成这个模块的 API 接口文档"
```

### 场景 4：需求讨论

```
/product-manager 我想给用户加一个单词本功能
# Claude 会追问：为什么需要？怎么用？多简单才算够？
# 最终输出可执行的 PRD
```

---



## 七、注意事项

### 7.1 Claude 不是你，你是决策者

- Claude 出方案 → 你审核确认 → Claude 执行
- 涉及数据库迁移、鉴权、支付等高危模块，必须你亲自把关
- AI 生成的代码和人类代码一样，要 review

### 7.2 任务粒度要小

一次只让 Claude 做一个功能点。不要一次丢给它整个模块，那样容易失控。

### 7.3 Claude 犯错怎么办？

立即纠正，然后让 Claude 把教训写入 CLAUDE.md 的「经验教训」章节。下次它就不会再犯。

### 7.4 善用 `!` 前缀

在 Claude Code 对话中，输入 `! <命令>` 可以直接在当前会话中执行系统命令：
```
! npm run dev
! git log --oneline
```
