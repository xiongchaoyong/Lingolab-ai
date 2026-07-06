# 项目启动配置指南

> 本文件是 Claude Code 在新环境中首次启动项目时的操作指南。
> Claude Code 应逐项检查并引导用户完成配置，每完成一项标记 ✅。

---

## 🎯 用户入口

用户拿到项目后，**只需要对 Claude Code 说一句话**即可启动：

> **"帮我启动这个项目"**

或任意等价的表达：
- "setup this project"
- "帮我配置并运行这个项目"
- "把项目跑起来"

Claude Code 会读取本指南，自动完成所有检测和配置，过程中会主动询问必要信息（数据库密码、API Key 等），用户无需提前知道任何技术细节。

---

## 前置检测

Claude Code 首先执行以下检测，判断哪些步骤需要执行：

```
检查清单：
□ Node.js >= 18        → 终端执行 node -v
□ Python >= 3.11       → 终端执行 python3 --version
□ MySQL 8+ 已安装且运行 → 终端执行 mysql --version && mysqladmin ping 2>/dev/null
□ FFmpeg 已安装         → 终端执行 ffmpeg -version
□ backend/.env 是否存在且已配置真实值
□ 数据库 english_training_dev 是否已创建
□ 数据库表是否已导入（检查表数量）
□ frontend/node_modules 是否存在
□ backend 虚拟环境是否存在
```

---

## 第一步：环境检测与软件安装

**Claude Code 执行：** 逐一运行前置检测中的命令。

**Claude Code 询问用户：**

> 检测到以下软件未安装：{缺失列表}。是否需要我提供安装指引？

对未安装的软件，根据操作系统给出安装命令：

| 软件 | macOS | Windows | Linux (Ubuntu) |
|------|-------|---------|----------------|
| Node.js | `brew install node` | 下载安装包 https://nodejs.org | `sudo apt install nodejs npm` |
| Python 3.11+ | `brew install python@3.12` | 下载安装包 https://python.org | `sudo apt install python3.12` |
| MySQL 8 | `brew install mysql && brew services start mysql` | 下载安装包 https://dev.mysql.com | `sudo apt install mysql-server-8.0` |
| FFmpeg | `brew install ffmpeg` | 下载并手动配置 PATH | `sudo apt install ffmpeg` |

---

## 第二步：配置数据库

### 2.1 创建数据库

**Claude Code 询问用户：**

> 请提供 MySQL 连接信息：
> - 主机地址（默认 localhost）：
> - 端口（默认 3306）：
> - 用户名（默认 root）：
> - 密码：

拿到密码后，Claude Code 执行：

```bash
mysql -u root -p"${MYSQL_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS english_training_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

确认创建成功后告知用户。

### 2.2 导入数据库结构和初始数据

项目提供了 `backend/init.sql`，包含完整的表结构 + 开发测试数据（包含可登录的测试账号）。

**Claude Code 执行：**

```bash
mysql -u root -p"${MYSQL_PASSWORD}" english_training_dev < backend/init.sql
```

### 2.3 确认 Alembic 版本对齐

init.sql 已包含实际表结构，但 Alembic 版本表可能不完整。**Claude Code 执行：**

```bash
cd backend && alembic stamp head
```

这会让 Alembic 将当前数据库结构标记为最新版本。

---

## 第三步：配置环境变量

### 3.1 后端 `.env`

**Claude Code 询问用户：**

> 需要配置以下后端环境变量：
>
> **1. 数据库密码（必填）**
>    你刚才输入的 MySQL 密码是什么？
>
> **2. 阿里百炼 API Key（必填，否则 AI 核心功能不可用）**
>    请提供你的阿里百炼 DashScope API Key。
>    如果没有，去 https://dashscope.aliyun.com 注册并获取。
>
> **3. JWT 密钥（可选，我会自动生成）**
>
> **4. HuggingFace 镜像（国内必填）**
>    你在国内吗？如果是，使用 https://hf-mirror.com 镜像加速模型下载。

拿到以上信息后，Claude Code 生成 `backend/.env`：

```env
# 数据库
DATABASE_URL=mysql+pymysql://{用户名}:{密码}@localhost:3306/english_training_dev

# AI 模型（阿里百炼 DashScope）— 必填
BAILIAN_API_KEY={API_KEY}

# JWT — 自动生成随机密钥
JWT_SECRET_KEY={随机生成的密钥}

# HuggingFace 镜像（国内加速）
HF_ENDPOINT=https://hf-mirror.com

# 语音合成（可选，Edge TTS 免费无需密钥）
DOUBAO_APP_ID=
DOUBAO_ACCESS_KEY=
```

### 3.2 前端 `.env.local`

**Claude Code 直接生成**（无需询问，本地开发默认配置）：

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 第四步：安装依赖

### 4.1 后端 Python 依赖

**Claude Code 执行：**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> ⚠️ PyTorch 约 2-3GB，首次安装较慢。Mac Apple Silicon 用户会自动使用 MPS 加速版本。

### 4.2 前端 Node.js 依赖

**Claude Code 执行：**

```bash
cd frontend
npm install
```

---

## 第五步：启动验证

### 5.1 启动后端

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**首次启动行为：**
- 自动加载知识图谱到内存
- 自动下载并加载发音评测模型（wav2vec2，约 1.5GB）
- 自动下载 ASR 模型（WhisperX small，约 500MB）
- 首次启动可能需要 3-5 分钟

**验证成功标志：** 控制台显示 "知识图谱加载完成" 和 "发音评测模型加载完成"。

### 5.2 启动前端

```bash
cd frontend
npm run dev
```

**验证成功标志：** 浏览器访问 http://localhost:5173 能打开登录页面。

---

## 测试账号

init.sql 导入了开发测试数据，包含以下可登录账号：

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin@lingolab.com | 有管理后台权限 |
| 教师 | teacher_wang | teacher_wang@lingolab.com | 教师端权限 |
| 学生 | xxxcy | 1846326845@qq.com | 学生端，有学习数据 |

> 其他测试用户密码均为 bcrypt 加密，如未记录明文则无法登录，需在注册页面重新注册。

---

## 常见问题

### Q: HuggingFace 模型下载失败
A: 确保 `.env` 中设置了 `HF_ENDPOINT=https://hf-mirror.com`（国内用户）。

### Q: PyTorch 安装报错
A: Mac 用户确保 Xcode Command Line Tools 已安装：`xcode-select --install`

### Q: MySQL 连接被拒
A: 检查 MySQL 服务是否已启动：
- macOS: `brew services start mysql`
- Linux: `sudo systemctl start mysql`

### Q: 端口被占用
A: 默认端口为 3306(MySQL)、5173(前端)、8000(后端)，如冲突可在配置中修改。

### Q: 首次启动后端超时
A: 模型下载可能较慢，耐心等待。如持续报错，检查网络或镜像设置。
