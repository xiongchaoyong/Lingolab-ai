# 模块 3：知识图谱驱动的个性化学习路径

> 实现日期：2026-06-24
> 技术栈：NetworkX（内存图）+ MySQL（持久化）+ FastAPI

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                              │
│  LearningPathView.vue  │  RecommendationView.vue                │
└──────────────┬──────────────────────┬───────────────────────────┘
               │ REST API             │ REST API
               ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                               │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ learning_path.py │  │ recommendation.py│  │  auth.py       │ │
│  │ GET /tasks        │  │ GET /            │  │ GET /profile/  │ │
│  │ POST /complete    │  │ POST /dislike    │  │   scores       │ │
│  │ POST /skip        │  │ POST /refresh    │  │ POST /refresh  │ │
│  └────────┬──────────┘  └────────┬─────────┘  └───────┬────────┘ │
│           │                      │                     │          │
│           ▼                      ▼                     ▼          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              RecommendationService (推荐引擎)               │  │
│  │  - 短板分析 → 四因子评分 → 每日任务生成                      │  │
│  └──────────┬─────────────────────────────┬───────────────────┘  │
│             │                             │                      │
│             ▼                             ▼                      │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │ KnowledgeGraph   │    │ ProfileUpdater (EMA 动态画像)     │   │
│  │ Service          │    │ - 分数摄入                        │   │
│  │ (NetworkX 内存图) │    │ - EMA 重算                       │   │
│  └────────┬─────────┘    │ - level_final 更新                │   │
│           │              └──────────────┬───────────────────┘   │
│           │                             │                        │
│           ▼                             ▼                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    MySQL 数据库                              │  │
│  │  kg_nodes / kg_edges / daily_tasks / user_skill_scores     │  │
│  │  material_recommendations / user_profiles                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. 知识图谱设计

### 2.1 节点类型（6 种）

| 类型 | 数量 | 说明 | ID 示例 |
|------|------|------|---------|
| `cefr_level` | 6 | CEFR 等级 A1-C2 | `cefr:A1`, `cefr:B1` |
| `skill` (phoneme) | 44 | 英语音素技能 | `skill:phoneme_θ`, `skill:phoneme_r` |
| `skill` (grammar) | 21 | 语法点技能 | `skill:grammar_present_perfect` |
| `skill` (vocabulary) | 12 | 词汇领域技能 | `skill:vocab_travel` |
| `topic` | 15 | 对话场景/话题 | `topic:restaurant`, `topic:travel` |
| `material` | 30 | 学习资料（视频/文章/音频各10） | `material:video_1`, `material:audio_5` |

**总计：129 个节点**

### 2.2 边类型（6 种）

| 边类型 | 数量 | 方向 | 含义 |
|--------|------|------|------|
| **BELONGS_TO** | 123 | 技能/资料/话题 → CEFR | 这个内容属于哪个难度等级 |
| **SIMILAR_TO** | 83 | 音素 ↔ 音素 | 容易混淆的音素对（如 /θ/ ↔ /ð/） |
| **TEACHES** | 36 | 资料 → 技能 | 这个资料教什么技能 |
| **HAS_PREREQ** | 25 | 技能 → 技能 | 学这个之前必须先学那个 |
| **COVERS** | 25 | 资料 → 话题 | 这个资料覆盖什么话题场景 |
| **PRACTICES** | 0 | 任务 → 技能 | 预留，任务练习什么技能 |

**总计：292 条边**

### 2.3 关系详解

#### BELONGS_TO（属于等级）
```
音素 /θ/  ──BELONGS_TO──▶  B1
语法 现在完成时 ──BELONGS_TO──▶  B1
视频 BBC News ──BELONGS_TO──▶  B2
话题 旅行 ──BELONGS_TO──▶  A2
```
**作用**：推荐时过滤掉难度不匹配的内容。

#### HAS_PREREQ（前置依赖）
```
现在完成时 ──HAS_PREREQ──▶ 一般过去时
（先学一般过去时，才能学现在完成时）

过去完成时 ──HAS_PREREQ──▶ 现在完成时
过去完成时 ──HAS_PREREQ──▶ 一般过去时
（过去完成时依赖两个前置）
```
**作用**：安排学习路径时保证顺序正确，不会把高级语法排在基础语法前面。

#### SIMILAR_TO（易混淆）
```
/θ/ (think)  ──SIMILAR_TO──▶  /ð/ (this)
/ɪ/ (ship)   ──SIMILAR_TO──▶  /iː/ (sheep)
/r/ (red)    ──SIMILAR_TO──▶  /l/ (let)
```
**作用**：用户在某个音素上得分低，推荐引擎顺带推荐易混淆音素的练习。

#### TEACHES（教授关系）
```
视频 Master TH Sound ──TEACHES──▶ 音素 /θ/
视频 Master TH Sound ──TEACHES──▶ 音素 /ð/
文章 Daily Routine ──TEACHES──▶ 词汇：日常生活
文章 Daily Routine ──TEACHES──▶ 语法：一般现在时
```
**作用**：推荐引擎找到用户弱项技能 → 反向查找哪些资料 TEACHES 这个技能 → 推荐。

#### COVERS（覆盖话题）
```
视频 Ordering Food ──COVERS──▶ 话题：餐厅点餐
音频 Airport Check-in ──COVERS──▶ 话题：机场值机
```
**作用**：用户兴趣是"旅行" → 找 COVERS 旅行话题的资料 → 匹配兴趣得分高。

---

## 3. 数据模型

### 3.1 数据库表

#### kg_nodes（知识图谱节点）
```sql
id          VARCHAR(64)  PRIMARY KEY   -- 如 skill:phoneme_θ
type        ENUM('skill','material','topic','cefr_level','task_type')
sub_type    VARCHAR(32)                -- phoneme/grammar/vocabulary/video/article/audio
label       VARCHAR(128) NOT NULL      -- 显示名称
extra_data  JSON                       -- 附加属性（cefr/tags/url/duration 等）
is_active   TINYINT     DEFAULT 1
created_at  DATETIME
updated_at  DATETIME
```

#### kg_edges（知识图谱边）
```sql
id          INT AUTO_INCREMENT PRIMARY KEY
source_id   VARCHAR(64)  FK → kg_nodes.id
target_id   VARCHAR(64)  FK → kg_nodes.id
relation    ENUM('HAS_PREREQ','BELONGS_TO','TEACHES','COVERS','SIMILAR_TO','PRACTICES')
weight      DECIMAL(5,2) DEFAULT 1.00
extra_data  JSON
is_active   TINYINT     DEFAULT 1
created_at  DATETIME
```

#### daily_tasks（每日任务）
```sql
id              INT AUTO_INCREMENT PRIMARY KEY
user_id         INT         FK → user_profiles.id
task_date       DATE        NOT NULL
task_type       ENUM('shadowing','conversation','listening')
title           VARCHAR(200)
description     TEXT
difficulty      VARCHAR(5)            -- CEFR 等级
focus_skill_id  VARCHAR(64) FK → kg_nodes.id
material_id     VARCHAR(64) FK → kg_nodes.id
scene           VARCHAR(32)           -- 对话场景标识
status          ENUM('pending','skipped','completed')
score           DECIMAL(5,2)
duration_seconds INT
skip_reason     VARCHAR(64)
completed_at    DATETIME
created_at      DATETIME
updated_at      DATETIME
```

#### user_skill_scores（用户技能分数 — 动态画像）
```sql
id          INT AUTO_INCREMENT PRIMARY KEY
user_id     INT         FK → user_profiles.id
dimension   VARCHAR(32)           -- listening/speaking/reading/grammar
skill_name  VARCHAR(128)          -- 如 pronunciation:phoneme_accuracy
score       DECIMAL(5,2)
source      VARCHAR(32)           -- pronunciation/conversation/daily_task
source_id   INT
created_at  DATETIME
```

#### material_recommendations（推荐记录）
```sql
id                INT AUTO_INCREMENT PRIMARY KEY
user_id           INT         FK → user_profiles.id
material_node_id  VARCHAR(64) FK → kg_nodes.id
recommend_date    DATE
recommend_score   DECIMAL(5,2)
reason_tags       JSON
action            ENUM('pending','viewed','completed','disliked')
viewed_at         DATETIME
created_at        DATETIME
```

### 3.2 维度映射

| 练习来源 | 具体技能 | 映射维度 |
|----------|----------|----------|
| 发音评测 | 音素准确度/重音/语调/连读/节奏 | **speaking** |
| AI 对话(语音) | 5 个声学维度 | **speaking** |
| AI 对话(文本) | 语法正确率 | **grammar** |
| AI 对话(文本) | 词汇丰富度 | **reading** |
| AI 对话(文本) | 对话参与度 | **speaking** |
| 每日跟读任务 | 任务完成 | **speaking** |
| 每日听力任务 | 任务完成 | **listening** |

---

## 4. 核心服务

### 4.1 KnowledgeGraphService（知识图谱服务）

**文件**：`backend/app/services/knowledge_graph.py`

单例模式，应用启动时从 MySQL 加载全量数据到 NetworkX 有向图，运行时所有读操作直接查内存。

**关键方法**：

| 方法 | 功能 |
|------|------|
| `load_from_db(db)` | 启动时从 MySQL 全量加载节点和边 |
| `get_node(id)` | 获取单个节点属性 |
| `get_nodes_by_type(type)` | 按类型获取节点列表 |
| `get_neighbors(id, relation, direction)` | 获取邻居节点（支持关系过滤和方向） |
| `get_prerequisites(skill_id)` | 获取技能的前置依赖（HAS_PREREQ 出边） |
| `get_similar_skills(skill_id)` | 获取易混淆技能（SIMILAR_TO 出边） |
| `get_materials_teaching(skill_id)` | 获取教授某技能的资料（TEACHES 入边） |
| `get_skills_by_cefr(level)` | 获取某 CEFR 等级的所有技能 |
| `get_materials_by_cefr(level)` | 获取某 CEFR 等级的资料 |
| `get_materials_covering_topic(topic_id)` | 获取覆盖某话题的资料（COVERS 入边） |
| `get_prerequisite_chain(skill_id)` | BFS + 拓扑排序获取完整前置链 |
| `shortest_path(a, b)` | 两节点最短路径 |
| `get_skills_for_dimension(dim)` | 获取某测评维度关联的技能节点 |
| `get_topics_by_tags(tags)` | 根据兴趣标签匹配场景 |

### 4.2 RecommendationService（推荐引擎）

**文件**：`backend/app/services/recommendation.py`

#### 四因子评分公式

```
总分 = 短板匹配 × 0.40 + 等级匹配 × 0.30 + 兴趣匹配 × 0.20 + 新颖度 × 0.10
```

| 因子 | 权重 | 计算方式 |
|------|------|----------|
| 短板匹配 | 40% | 资料 TEACHES 的技能 ∩ 用户弱项技能 → 越重叠分越高 |
| 等级匹配 | 30% | CEFR 等级差：同级=1.0, 差1级=0.6, 差2级=0.3, 差3+级=0.1 |
| 兴趣匹配 | 20% | 资料标签 ∩ 用户兴趣标签 → 越重叠分越高 |
| 新颖度 | 10% | 7天内推荐过扣分，被dislike直接0分 |

#### 短板分析

```
优先级：
1. UserSkillScore EMA 动态分数（最近30天练习数据）
2. AssessmentRecord 测评记录（初始测评）
3. 默认 "speaking"
```

#### 每日任务生成（六步流程）

```
Step 1: 短板优先 → 取 EMA 最低的维度
Step 2: 目标加权 → learning_goal 映射场景偏好
Step 3: CEFR 匹配 → 图查找同等级内容
Step 4: 前置依赖 → 检查技能是否已掌握
Step 5: 兴趣优选 → 资料标签 ∩ 用户兴趣
Step 6: 写入 daily_tasks 表
```

每天生成 3 个任务：

| 任务类型 | 基于 | 选择逻辑 |
|----------|------|----------|
| **跟读 (shadowing)** | 音素技能 | 短板技能 ∩ CEFR 同等级音素 → 找最佳资料 |
| **对话 (conversation)** | 话题场景 | 学习目标 → 偏好场景，回退到随机同等级场景 |
| **听力 (listening)** | 音频资料 | 同等级音频，按兴趣+场景覆盖+难度匹配打分 |

### 4.3 ProfileUpdater（动态画像更新）

**文件**：`backend/app/services/profile_updater.py`

#### EMA 算法

```
EMA_new = score × 0.3 + EMA_old × 0.7
```

- 只计算最近 **30 天** 数据
- 新分数权重 0.3，旧分数权重 0.7
- 自然给近期表现更高权重

#### CEFR 定级阈值

| 分数区间 | 等级 |
|----------|------|
| 96-100 | C2 |
| 81-95 | C1 |
| 61-80 | B2 |
| 41-60 | B1 |
| 21-40 | A2 |
| 0-20 | A1 |

#### 分数摄入入口

| 方法 | 触发时机 | 写入记录数 |
|------|----------|------------|
| `ingest_pronunciation_scores()` | 发音评测完成 | 5 条（5 个发音维度 → speaking） |
| `ingest_conversation_scores()` | AI 对话结束 | 8 条（5 语音 + 3 文本维度） |
| `ingest_task_score()` | 每日任务完成 | 1 条（任务类型 → 对应维度） |

每次摄入后自动调用 `recalculate()` 更新 `user_profiles.level_final`。

---

## 5. 推荐链路示例

假设用户**小明**：
- 当前等级：B1（由 EMA 动态计算）
- 弱项维度：speaking（EMA 分数 38，最低）
- 学习目标：日常交流
- 兴趣标签：旅行、音乐

### 链路步骤

```
Step 1: 短板分析
  EMA 分数: listening=72, speaking=38, reading=65, grammar=58
  → 弱项 = speaking

Step 2: 图遍历 — 查找 speaking 关联的技能
  speaking → 映射到音素类技能 (phoneme)
  → 在 B1 等级下查找：/θ/, /ð/, /ʒ/, /dʒ/, /ɜ/, /ə/, /ɪə/, /eə/ ...

Step 3: 反向查找教授这些技能的资料
  沿 TEACHES 入边：
    视频 A (Master TH Sound) ──TEACHES──▶ /θ/, /ð/
    视频 B (Speak Naturally)  ──TEACHES──▶ /eɪ/, /oʊ/, /ə/
    ...

Step 4: 四因子打分（以视频 A 为例）
  短板匹配 40%: /θ/ /ð/ ∈ speaking 弱项 → 满分 40
  等级匹配 30%: B1 = B1 → 满分 30
  兴趣匹配 20%: 标签"发音" ∉ [旅行, 音乐] → 0
  新颖度 10%:    未推荐过 → 满分 10
  ────────────────────────────
  总分: 40 + 30 + 0 + 10 = 80

  以视频 D (Travel English) 为例：
  短板匹配 40%: 教 vocab_travel 不属于 speaking 弱项 → 低分 8
  等级匹配 30%: A2 vs B1，差1级 → 18
  兴趣匹配 20%: 标签"旅行" ∈ [旅行, 音乐] → 满分 20
  新颖度 10%:    未推荐过 → 10
  ────────────────────────────
  总分: 8 + 18 + 20 + 10 = 56

Step 5: 排序输出
  最终取各类别 Top 2：
    视频: [Speak Naturally(85), Master TH Sound(80)]
    文章: [London Trip(72), Daily Routine(65)]
    音频: [Restaurant Ordering(90), Airport Check-in(78)]
```

### 链路图

```
用户画像
  ├─ level_final = B1        ← ProfileUpdater EMA 动态更新
  ├─ 弱项 = speaking         ← 推荐引擎读取 EMA 分数
  └─ 兴趣 = [旅行, 音乐]     ← 注册时填写
         │
         ▼
┌──────────────────────────────────────────────────┐
│              知识图谱 图遍历                       │
│                                                  │
│  speaking 弱项 → 音素技能(B1)                      │
│     │                                            │
│     │ BELONGS_TO (过滤等级)                        │
│     ▼                                            │
│  音素技能(B1) ← TEACHES (反向查找) ← 学习资料       │
│                                          │       │
│                                          │ COVERS│
│                                          ▼       │
│                                      话题"旅行"   │
│                                      ↑ 匹配兴趣   │
│                                                  │
│  四因子打分 → 排序 → Top 6 推荐                    │
└──────────────────────────────────────────────────┘
         │
         ▼
  前端推荐页面展示 6 条个性化推荐
```

---

## 6. API 接口

### 6.1 每日任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/learning/tasks` | 获取今日任务列表（含进度） |
| POST | `/api/learning/tasks/{id}/complete` | 完成任务（记录分数，触发画像更新） |
| POST | `/api/learning/tasks/{id}/skip` | 跳过任务（可带原因） |
| POST | `/api/learning/tasks/{id}/replace` | 换一个同类型任务 |
| POST | `/api/learning/tasks/{id}/adjust-difficulty` | 调整任务难度 ±1 级 |
| GET | `/api/learning/history?days=7` | 获取历史学习记录 |

### 6.2 资料推荐

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/recommendations/` | 获取今日推荐（视频/文章/音频各2条） |
| POST | `/api/recommendations/{id}/dislike` | 标记不感兴趣 |
| POST | `/api/recommendations/refresh` | 换一批推荐 |
| POST | `/api/recommendations/{id}/click` | 记录点击/完成 |

### 6.3 动态画像

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/profile/scores` | 获取 EMA 各维度分数 + 最近记录 |
| POST | `/api/auth/profile/refresh` | 手动触发画像重算 |

---

## 7. 启动流程

```
1. FastAPI 启动 → lifespan 事件
2. 创建 SessionLocal → 连接 MySQL
3. kg_service.load_from_db(db) → 全量加载节点/边到 NetworkX
4. 打印日志：[KnowledgeGraph] 已加载 129 节点, 292 边
5. 注册路由：learning_path, recommendation, auth
6. 服务就绪，等待请求
```

### 种子数据

```bash
cd backend
python seed_kg.py
```

种子数据采用**两阶段插入**：
- 阶段 1：先插入全部 129 个节点（每类节点插入后 flush）
- 阶段 2：再插入全部 292 条边（确保所有 FK 引用已存在）

---

## 8. 文件清单

| 文件 | 说明 |
|------|------|
| `backend/seed_kg.py` | 种子数据（129 节点 + 292 边） |
| `backend/app/models/knowledge_graph.py` | ORM 模型（KGNode/KGEdge/DailyTask/MaterialRecommendation） |
| `backend/app/models/profile.py` | UserSkillScore ORM 模型 |
| `backend/app/services/knowledge_graph.py` | KnowledgeGraphService（NetworkX 内存图） |
| `backend/app/services/recommendation.py` | RecommendationService（推荐引擎 + 任务生成） |
| `backend/app/services/profile_updater.py` | ProfileUpdater（EMA 动态画像更新） |
| `backend/app/api/learning_path.py` | 每日任务 API 路由 |
| `backend/app/api/recommendation.py` | 资料推荐 API 路由 |
| `backend/app/api/auth.py` | 用户 API（含 profile/scores 和 profile/refresh） |
| `backend/app/schemas/learning_path.py` | 学习路径 Pydantic Schema |
| `backend/app/schemas/profile.py` | 画像分数 Pydantic Schema |
| `backend/main.py` | FastAPI 入口（KG 加载 + 路由注册） |
| `frontend/src/api/learning_path.js` | 前端学习路径 API 封装 |
| `frontend/src/api/recommendation.js` | 前端推荐 API 封装 |
| `frontend/src/stores/learning_path.js` | 前端 Pinia Store |
| `frontend/src/views/learning/LearningPathView.vue` | 学习路径页面 |
| `frontend/src/views/learning/RecommendationView.vue` | 资料推荐页面 |