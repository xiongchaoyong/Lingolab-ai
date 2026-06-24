# 模块 1+2：用户认证与英语水平测评

> 实现日期：2026-05 ~ 2026-06
> 技术栈：FastAPI + JWT + bcrypt + MySQL

---

## 1. 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                             │
│  RegisterView → LoginView → AssessmentView → HomeView        │
└──────────────┬──────────────────────┬────────────────────────┘
               │ REST API             │ REST API
               ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                             │
│                                                              │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ auth.py              │  │ assessment.py                │  │
│  │ POST /register       │  │ POST /start                  │  │
│  │ POST /login          │  │ POST /submit                 │  │
│  │ GET  /profile        │  └──────────┬───────────────────┘  │
│  │ PUT  /profile        │             │                      │
│  │ GET  /profile/scores │             ▼                      │
│  │ POST /profile/refresh│  ┌──────────────────────────────┐  │
│  └──────────┬───────────┘  │ 评分逻辑 (assessment.py 内)   │  │
│             │              │ - 客观题：选项比对             │  │
│             ▼              │ - 口语题：占位 60 分           │  │
│  ┌──────────────────┐     │ - CEFR 定级                   │  │
│  │ JWT 认证中间件     │     │ - 短板检测                    │  │
│  │ - create_token    │     └──────────────────────────────┘  │
│  │ - get_current_user│                                        │
│  └──────────────────┘                                        │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    MySQL 数据库                        │   │
│  │  user_profiles / assessment_questions                 │   │
│  │  assessment_records / user_skill_scores               │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 用户认证

### 2.1 注册流程

```
用户填写表单 → POST /api/auth/register → 校验 → 创建用户 → 返回 JWT
```

**校验规则**：
- 用户名唯一性检查（409 冲突）
- 邮箱唯一性检查（409 冲突）
- 密码经过 bcrypt 哈希存储

**注册时自动计算**：
- `age_group`：根据年龄归类（`get_age_group()`）
- `learning_goal`：前端英文值 → 中文存储（`LEARNING_GOAL_MAP`）
- `role`：固定为 `"learner"`
- `assessment_completed`：初始化为 `0`

**返回**：`{user_id, username, token, assessment_completed: false, age_group}`

### 2.2 登录流程

```
用户填写表单 → POST /api/auth/login → 验证密码 → 检查账号状态 → 返回 JWT
```

**返回**：
```json
{
  "user_id": 1,
  "username": "xiaoming",
  "token": "eyJ...",
  "assessment_completed": false,
  "redirect": "/assessment"   // 未测评 → /assessment，已测评 → /home
}
```

### 2.3 JWT 认证

**文件**：`backend/app/core/security.py`

| 函数 | 用途 |
|------|------|
| `hash_password(pwd)` | bcrypt 哈希密码 |
| `verify_password(pwd, hash)` | 验证密码 |
| `create_access_token(user_id, username)` | 生成 JWT（包含 user_id + username） |
| `get_current_user(token)` | FastAPI Depends，从 Authorization Header 解析 JWT → 查库返回 UserProfile |
| `get_age_group(age)` | 年龄 → 年龄段映射 |
| `LEARNING_GOAL_MAP` | 学习目标英文→中文映射字典 |

### 2.4 用户画像 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/profile` | 获取当前用户完整画像 |
| PUT | `/api/auth/profile` | 修改学习目标 + 兴趣标签（乐观锁防并发） |
| GET | `/api/auth/profile/scores` | 获取 EMA 动态技能分数 + 最近记录 |
| POST | `/api/auth/profile/refresh` | 手动触发画像重算 |

---

## 3. 水平测评

### 3.1 数据模型

#### assessment_questions 表

```sql
id              INT AUTO_INCREMENT PRIMARY KEY
question_text   TEXT NOT NULL              -- 题目内容
options         JSON NOT NULL              -- ["A. xxx", "B. xxx", ...] 口语题为 []
correct_option  TINYINT NOT NULL           -- 1-4，口语题无效
dimension       ENUM('listening','speaking','reading','grammar')
difficulty      VARCHAR(5)                 -- CEFR: A1/A2/B1/B2/C1/C2
is_active       TINYINT DEFAULT 1
```

#### assessment_records 表

```sql
id              INT AUTO_INCREMENT PRIMARY KEY
user_id         INT FK → user_profiles.id
session_id      VARCHAR(36) NOT NULL       -- 一次测评的 UUID
question_id     INT FK → assessment_questions.id
question_type   ENUM('multiple_choice','speaking')
user_answer     TEXT                       -- 客观题: "A"/"B"/"C"/"D"，口语题: 音频URL
is_correct      TINYINT                    -- 1/0，口语题为 NULL
score           DECIMAL(5,2)               -- 0-100
audio_url       VARCHAR(500)               -- 口语题音频路径
transcript      TEXT                       -- 口语题 ASR 转录
question_order  TINYINT                    -- 1-10
```

### 3.2 测评流程

```
Step 1: POST /api/assessment/start
  → 生成 UUID session_id
  → 从题库按维度取题（listening×3, speaking×3, reading×2, grammar×2 = 10题）
  → 返回 {session_id, questions: [{id, type, difficulty, content, options}]}

Step 2: 前端逐题展示，用户答题
  → 客观题：4选1
  → 口语题：录音上传（当前占位，未真正评分）

Step 3: POST /api/assessment/submit
  → 接收 session_id + answers JSON
  → 逐题评分 → 写入 assessment_records
  → 计算维度平均分 → 综合分 → CEFR 定级 → 短板检测
  → 更新 user_profiles (level_test, level_final, assessment_completed=1)
  → 返回 {level, level_label, dimension_scores, overall_score, weakness, suggestion}
```

### 3.3 评分算法

#### 客观题评分
```python
correct_letter = chr(64 + question.correct_option)  # 1→A, 2→B, 3→C, 4→D
if answer == correct_letter:
    score = 100.0, is_correct = 1
else:
    score = 0.0, is_correct = 0
```

#### 口语题评分（当前占位）
```python
score = 60.0   # 硬编码，待集成 ASR + LLM 评分
is_correct = None
```

#### 综合分计算
```python
# 1. 按维度求平均
dimension_scores = {
    "listening": avg([题目1, 题目2, 题目3]),
    "speaking":  avg([题目4, 题目5, 题目6]),
    "reading":   avg([题目7, 题目8]),
    "grammar":   avg([题目9, 题目10]),
}

# 2. 四维度等权平均
overall = sum(dimension_scores.values()) / 4
```

#### CEFR 定级阈值

| 分数区间 | 等级 | 标签 |
|----------|------|------|
| 96-100 | C2 | 精通 |
| 81-95 | C1 | 高级 |
| 61-80 | B2 | 中高级 |
| 41-60 | B1 | 中级 |
| 21-40 | A2 | 基础 |
| 0-20 | A1 | 入门 |

#### 短板检测
```python
weakness_dim = min(dimension_scores, key=dimension_scores.get)
# 返回最低分维度 + 中文建议
```

| 短板维度 | 建议 |
|----------|------|
| listening | 建议每天听15分钟英语播客或新闻 |
| speaking | 建议多进行口语练习 |
| reading | 建议每天阅读一篇英语短文 |
| grammar | 建议系统复习基础语法知识 |

### 3.4 测评后用户画像更新

```python
user.level_test = level          # 初始测评等级（固定不变）
user.level_final = level         # 动态等级（初始=测评等级，后续被 EMA 更新）
user.assessment_completed = 1    # 标记已完成测评
```

---

## 4. 用户画像结构

### user_profiles 表关键字段

```sql
id                    INT PRIMARY KEY
username              VARCHAR(64) UNIQUE
email                 VARCHAR(128) UNIQUE
password_hash         VARCHAR(256)
age                   INT
age_group             VARCHAR(32)       -- 年龄段
learning_goal         VARCHAR(64)       -- 学习目标（中文）
interests             JSON              -- 兴趣标签数组
level_self            VARCHAR(5)        -- 自评等级
level_test            VARCHAR(5)        -- 测评等级（固定）
level_final           VARCHAR(5)        -- 动态等级（EMA 更新）
assessment_completed  TINYINT           -- 0/1
role                  VARCHAR(16)       -- learner/admin
version               INT              -- 乐观锁版本号
is_active             TINYINT
```

### 学习目标映射

| 前端值 | 中文存储 |
|--------|----------|
| `daily_communication` | 日常交流 |
| `exam` | 考试 |
| `business` | 商务 |
| `abroad` | 出国 |
| `hobby` | 兴趣爱好 |

### 兴趣标签

用户注册时可选填的兴趣标签，如 `["旅行", "音乐", "科技", "美食"]`，用于推荐引擎的兴趣匹配因子。

---

## 5. 与动态画像的衔接

初始测评设置 `level_final` 后，后续每次练习（发音评测、对话、每日任务）都会通过 `ProfileUpdater` 用 EMA 算法更新 `level_final`：

```
初始测评 → level_final = B1
    ↓
用户练习发音 → EMA 重算 → speaking 分数上升
    ↓
用户练习对话 → EMA 重算 → grammar 分数上升
    ↓
level_final 可能从 B1 升到 B2
```

详见：`docs/module-3-knowledge-graph.md` 第 4.3 节 ProfileUpdater。

---

## 6. 文件清单

| 文件 | 说明 |
|------|------|
| `backend/app/api/auth.py` | 认证 API（注册/登录/画像/动态分数） |
| `backend/app/api/assessment.py` | 测评 API（开始/提交/评分/CEFR 定级） |
| `backend/app/core/security.py` | JWT + bcrypt + 认证中间件 |
| `backend/app/models/user.py` | UserProfile ORM 模型 |
| `backend/app/models/assessment.py` | AssessmentQuestion + AssessmentRecord ORM |
| `backend/app/models/profile.py` | UserSkillScore ORM |
| `backend/app/schemas/auth.py` | 认证相关 Pydantic Schema |
| `backend/app/schemas/assessment.py` | 测评相关 Pydantic Schema |
| `backend/app/schemas/profile.py` | 画像分数 Pydantic Schema |
| `backend/seed_assessment.py` | 测评题库种子数据（10 题） |
| `backend/sql/init.sql` | 数据库 DDL |
| `frontend/src/stores/auth.js` | 前端认证 Store |
| `frontend/src/stores/assessment.js` | 前端测评 Store |
| `frontend/src/views/auth/` | 注册/登录页面 |
| `frontend/src/views/assessment/` | 测评页面 |

---

## 7. 已知限制

1. **口语题评分为占位符**（硬编码 60 分），ASR 和 LLM 服务已就绪但未集成到测评提交流程
2. **题库为固定顺序**（按 id 排序），不是随机出题
3. **四个维度权重相等**，未根据学习目标差异化
4. **测评提交不调用 ProfileUpdater EMA**，测评分数与后续练习分数脱节
5. **用户可以重复测评**，无防重复机制