# AI 协作开发规范 v1.0

> 本规范基于模块2（英语水平智能测评）和模块4/6（发音评测/智能对话）的实际开发经验提炼，
> 供小组成员使用 AI 辅助开发时统一遵循。AI 在生成代码时应严格参照本规范中的模式。

---

## 目录

1. [项目结构规范](#1-项目结构规范)
2. [前端开发规范](#2-前端开发规范)
3. [后端开发规范](#3-后端开发规范)
4. [前后端协作规范](#4-前后端协作规范)
5. [开发工作流规范](#5-开发工作流规范)
6. [AI 提示词模板](#6-ai-提示词模板)

---

## 1. 项目结构规范

### 1.1 前端目录结构

```
frontend/src/
├── api/                      # Axios 请求封装，按模块拆分
│   ├── index.js              # Axios 实例 + 拦截器（统一入口）
│   ├── auth.js
│   ├── pronunciation.js
│   └── {module}.js           # 新模块按此模式新增
├── assets/styles/            # 全局样式
│   ├── tokens.css            # CSS 设计令牌（颜色/间距/圆角/字号）
│   ├── variables.scss        # SCSS 变量
│   ├── global.scss           # 全局样式 + 布局类（.immersive-layout 等）
│   ├── element-override.scss # Element Plus 主题覆盖
│   └── mixins.scss           # SCSS mixin
├── components/
│   ├── common/               # 跨模块复用的通用组件
│   │   ├── VoiceRecorder.vue
│   │   ├── DimensionBars.vue
│   │   └── ScoreBar.vue
│   ├── layout/               # 布局壳组件
│   │   ├── TopNavLayout.vue  # 顶部导航布局（主要使用）
│   │   ├── AppLayout.vue
│   │   ├── TopHeader.vue
│   │   └── SidebarNav.vue
│   └── {module}/             # 模块专属组件（如 pronunciation/）
├── router/
│   └── index.js              # 路由配置 + 导航守卫
├── stores/                   # Pinia 状态管理，按模块拆分
│   ├── auth.js
│   ├── app.js
│   └── {module}.js           # 新模块按此模式新增
└── views/                    # 页面级组件，按模块分目录
    ├── assessment/
    │   ├── AssessmentView.vue
    │   └── AssessmentResult.vue
    └── {module}/
        └── {Module}View.vue
```

### 1.2 后端目录结构

```
backend/
├── main.py                   # FastAPI 入口 + lifespan + 路由注册
├── requirements.txt
├── .env.example              # 环境变量模板（不提交 .env）
└── app/
    ├── api/                  # 路由层（薄层：解析请求→调用服务→返回响应）
    │   ├── __init__.py
    │   ├── pronunciation.py
    │   └── {module}.py       # 新模块按此模式新增
    ├── services/             # 业务逻辑层（厚层：AI/ML/算法）
    │   ├── __init__.py
    │   ├── pronunciation.py   # 单例模式的服务
    │   ├── asr.py
    │   ├── llm.py
    │   └── tts.py
    ├── schemas/              # Pydantic 请求/响应模型
    │   ├── __init__.py
    │   └── {module}.py       # 新模块按此模式新增
    ├── models/               # SQLAlchemy ORM 模型（数据库表）
    │   └── __init__.py
    └── core/
        ├── config.py         # Pydantic Settings（读取环境变量）
        └── database.py       # SQLAlchemy engine + session
```

### 1.3 命名规范速查表

| 层级 | 规范 | 示例 |
|------|------|------|
| Vue 组件文件 | PascalCase | `AssessmentView.vue` |
| 模板中使用 | PascalCase | `<AssessmentView />` |
| 前端 API 文件 | camelCase | `pronunciation.js` |
| Pinia store 文件 | camelCase | `assessment.js` |
| 后端 Python 文件 | snake_case | `pronunciation.py` |
| 后端类名 | PascalCase | `PronunciationService` |
| 后端函数/变量 | snake_case | `score_audio()` |
| API 路由路径 | kebab-case | `/api/pronunciation/score` |
| 数据库表名 | 复数 snake_case | `assessment_results` |

---

## 2. 前端开发规范

### 2.1 Vue 组件模式

**必须使用 `<script setup>` + Composition API，禁止 Options API。**

```vue
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useXxxStore } from '@/stores/xxx'

// 1. 路由 & store 初始化
const router = useRouter()
const store = useXxxStore()

// 2. 响应式状态（ref / reactive）
const localState = ref(null)
const isLoading = ref(false)

// 3. 计算属性（computed）
const derived = computed(() => { /* ... */ })

// 4. 方法（function）
function handleAction() { /* ... */ }

// 5. 生命周期
onMounted(() => { /* ... */ })
onUnmounted(() => { /* 清理定时器等 */ })
</script>

<template>
  <!-- 模板内容 -->
</template>

<style lang="scss" scoped>
/* 组件样式，使用 CSS 变量 */
</style>
```

### 2.2 组件组织原则

- **页面组件** (`views/`)：对应路由，负责组装子组件和调用 store
- **通用组件** (`components/common/`)：跨模块复用，通过 props/emit 通信
- **模块组件** (`components/{module}/`)：模块内复用
- **布局组件** (`components/layout/`)：页面壳，使用 `<router-view />` 嵌套

**组件拆分粒度**：当一个页面超过 300 行、或存在可复用的 UI 片段（如录音按钮、评分条）时，抽离为独立组件。

### 2.3 组件通信模式

```vue
<!-- 父 → 子：props -->
<VoiceRecorder :prep-time="15" :max-duration="45" />

<!-- 子 → 父：emit -->
const emit = defineEmits(['start', 'stop', 'complete'])
emit('complete', { blob, mimeType, elapsed })

<!-- 子暴露方法给父调用 -->
defineExpose({ reset, setScored })
```

**原则**：父子通信用 props/emit，跨组件共享状态用 Pinia store，不依赖全局事件总线。

### 2.4 Pinia Store 模式

**必须使用 Composition API 风格（`defineStore('name', () => { ... })`）**

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 常量定义放在 store 外部
const TYPE_LABELS = { /* ... */ }

export const useXxxStore = defineStore('xxx', () => {
  // ===== 状态（ref） =====
  const data = ref(null)
  const isLoading = ref(false)

  // ===== 计算属性（computed） =====
  const hasData = computed(() => data.value !== null)

  // ===== 方法（function） =====
  async function fetchData() {
    isLoading.value = true
    try {
      // API 调用
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    data.value = null
  }

  // ===== 返回 =====
  return {
    data, isLoading,
    hasData,
    fetchData, reset,
  }
})
```

**关键规则**：
- 状态用 `ref()`，派生用 `computed()`，操作用 `function`
- store 是唯一的数据源，组件不直接调 API
- 跨页面持久化用 `localStorage`（如测评进度恢复）
- 敏感数据不存 localStorage

### 2.5 API 层模式

**统一入口** `api/index.js`：封装 axios 实例，自动附加 JWT + 统一错误处理。

**模块 API 文件**（如 `api/pronunciation.js`）：

```javascript
import request from './index'

// JSON 请求（非文件上传）
export function someJsonApi(param1, param2) {
  return request.post('/api/module/endpoint', { param1, param2 })
}

// 文件上传（音频/图片等）
export function uploadFile(blob, text) {
  const form = new FormData()
  form.append('audio', blob, 'recording.wav')
  form.append('text', text)
  return request.post('/api/module/endpoint', form, {
    timeout: 30000,  // 必要时自定义超时
  })
}

// SSE 流式请求（直接 fetch，不走 axios）
export async function streamApi(params, callbacks) {
  const resp = await fetch(`${API_BASE}/api/module/stream/endpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  // 手动解析 SSE 流...
}
```

**关键规则**：
- 所有 API 调用统一通过 `api/` 层，组件不直接调 axios
- 文件上传用 `FormData`，JSON 请求用 `Content-Type: application/json`
- SSE 流式请求用原生 `fetch`（axios 不支持流）
- 请求超时默认 30s，AI 评分等耗时操作适当延长

### 2.6 路由配置模式

```javascript
// 独立全屏路由（无导航布局）— 如测评、登录
{
  path: '/assessment',
  name: 'Assessment',
  component: () => import('@/views/assessment/AssessmentView.vue'),
  meta: { auth: true },
}

// 带导航布局的路由 — 大部分功能页面
{
  path: '/',
  component: () => import('@/components/layout/TopNavLayout.vue'),
  children: [
    {
      path: 'pronunciation',
      name: 'Pronunciation',
      component: () => import('@/views/pronunciation/PronunciationView.vue'),
      meta: { title: '发音评测', auth: true },
    },
  ],
}
```

**路由 meta 约定**：
- `auth: true` — 需要登录
- `guest: true` — 仅未登录可访问（登录/注册页）
- `role: 'teacher' | 'admin'` — 角色限制
- `title: '页面标题'` — 用于导航面包屑

### 2.7 样式规范

```scss
<style lang="scss" scoped>
// 必须使用 scoped，避免样式泄露
// 颜色使用 CSS 变量，禁止硬编码色值
.my-component {
  background: var(--color-bg-primary);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);

  // 穿透 Element Plus 组件样式
  :deep(.el-radio) {
    width: 100%;
  }
}
</style>
```

**CSS 变量体系**（定义在 `tokens.css`）：
- 颜色：`--color-primary`, `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, `--color-text-primary/secondary/disabled`, `--color-bg-primary/secondary`, `--color-border`
- 间距：`--spacing-xs/sm/md/lg/xl/xxl/xxxl`
- 圆角：`--radius-sm/md/lg`
- 字号：`--font-size-sm/base/lg/xl`

**得分颜色约定**：>= 80 绿色，>= 60 黄色，< 60 红色

### 2.8 错误处理与边界情况

```vue
<script setup>
// 1. 数据不存在时给出合理默认值
const report = computed(() => store.report)

// 2. 页面挂载时检查数据完整性
onMounted(() => {
  if (!store.report) {
    store.completeAssessment()  // 兜底生成
  }
})

// 3. 空状态展示
// 在模板中用 v-if/v-else 区分 loading / empty / error / normal 四种状态
</script>

<template>
  <!-- 加载中 -->
  <el-skeleton v-if="loading" :rows="5" animated />
  <!-- 空数据 -->
  <el-empty v-else-if="!data" description="暂无数据" />
  <!-- 正常 -->
  <div v-else>...</div>
</template>
```

### 2.9 录音组件使用规范

项目使用 `VoiceRecorder.vue` 统一录音组件，不要在其他组件中直接调用 `navigator.mediaDevices.getUserMedia()`。

**Props**：`prepTime`（准备秒数，默认3）、`maxDuration`（最大录音时长，默认45s）

**Events**：`@complete` 回调参数 `{ blob, mimeType, elapsed }`

---

## 3. 后端开发规范

### 3.1 FastAPI 路由模式

```python
"""模块名 API 路由"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.xxx import XxxRequest, XxxResponse
from app.services.xxx import do_something

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/endpoint", response_model=XxxResponse)
async def endpoint_name(
    param1: str = Form(..., description="参数说明"),
    file: UploadFile = File(None, description="上传文件说明"),
):
    """
    接口中文说明，描述功能和使用场景。
    """
    # 1. 参数校验
    if not param1 or not param1.strip():
        raise HTTPException(status_code=422, detail="参数不能为空")

    # 2. 调用业务服务
    try:
        result = await do_something(param1)
        return XxxResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        logger.error(f"服务错误: {e}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
```

**关键规则**：
- 路由文件是**薄层**，只负责：参数校验 → 调用服务 → 返回响应
- 所有接口使用 `POST`（即使语义上是读取操作）
- 中文注释 + 英文变量名
- 错误用 `HTTPException`，区分 422（参数错误）、503（服务不可用）、500（内部错误）
- 临时文件在 `finally` 块中清理

### 3.2 服务层模式

**AI/ML 模型服务使用单例模式**：

```python
"""模块服务"""

import logging

logger = logging.getLogger(__name__)

_service_instance = None

def get_xxx_service():
    """获取服务单例（懒加载模型）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = XxxService()
    return _service_instance


class XxxService:
    def __init__(self):
        """加载模型（启动时可能较慢）"""
        self.model = load_model()

    def process(self, input_data):
        """核心处理逻辑"""
        pass
```

**同步耗时操作（AI/ML 推理）用线程池包装**：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def score_audio(audio_path, text, mode):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = await loop.run_in_executor(
            pool, service.score, audio_path, text, mode
        )
    return result
```

### 3.3 Pydantic Schema 模式

```python
"""模块名 — 请求/响应 Schema"""

from typing import List, Optional
from pydantic import BaseModel, Field


class XxxRequest(BaseModel):
    """请求体"""
    text: str = Field(..., description="参数说明")
    mode: str = Field(default="default", description="可选参数，带默认值")


class XxxResponse(BaseModel):
    """响应体"""
    overall: float = Field(..., description="综合得分 (0-100)")
    details: List[DetailItem] = Field(default_factory=list, description="详细项列表")
    metadata: Optional[Metadata] = Field(default=None, description="可选元数据")
```

**关键规则**：
- 每个字段必须有 `description`
- 可选字段用 `Optional` + `default`
- 列表字段用 `default_factory=list`（不用 `[]`）
- 嵌套结构单独定义 BaseModel

### 3.4 路由注册模式

在 `main.py` 的 lifespan 中预加载模型，在底部注册路由：

```python
# main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时预加载模型"""
    try:
        from app.services.xxx import get_xxx_service
        get_xxx_service()
        logger.info("XXX 模型加载完成")
    except Exception as e:
        logger.warning(f"XXX 模型加载失败（可启动后重试）: {e}")
    yield

# 注册路由
from app.api.xxx import router as xxx_router
app.include_router(xxx_router, prefix="/api/xxx", tags=["中文标签"])
```

### 3.5 文件上传处理模式

```python
import tempfile
import os

@router.post("/upload-endpoint")
async def upload_endpoint(
    audio: UploadFile = File(..., description="上传文件"),
    text: str = Form(..., description="附加参数"),
):
    tmp_path = None
    try:
        suffix = os.path.splitext(audio.filename)[1] or ".default"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 处理文件...
        result = process(tmp_path, text)
        return result

    finally:
        # 清理临时文件
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
```

---

## 4. 前后端协作规范

### 4.1 开发顺序

**推荐顺序**：后端 Schema 定义 → 后端 API 路由 → 后端 Service 实现 → 前端 API 封装 → 前端 Store → 前端页面

在实际 AI 辅助开发中，可以：
1. **先定义 Schema**（前后端契约）：在一轮对话中让 AI 同时生成前端的类型定义和后端的 Pydantic Schema
2. **后端优先**：先实现后端 API 并手动测试通过
3. **前端接入**：后端可用后，再开发前端页面接入真实 API

### 4.2 请求/响应格式约定

| 场景 | 请求方式 | Content-Type |
|------|----------|-------------|
| 纯数据请求 | POST JSON | `application/json` |
| 文件上传 | POST FormData | `multipart/form-data` |
| 流式响应 | POST JSON/FormData | 接收 `text/event-stream` |

**响应格式**：后端直接返回数据对象，前端 axios 拦截器自动解包 `response.data`。

### 4.3 模块开发检查清单

每完成一个模块的开发，确保以下内容就绪：

**前端**：
- [ ] `api/{module}.js` — API 请求封装
- [ ] `stores/{module}.js` — Pinia store（如需要）
- [ ] `views/{module}/` — 页面组件
- [ ] `components/{module}/` — 模块专属组件（如需要）
- [ ] `router/index.js` — 路由注册 + meta 配置
- [ ] 组件复用：优先使用 `components/common/` 已有组件

**后端**：
- [ ] `app/schemas/{module}.py` — Pydantic 模型
- [ ] `app/api/{module}.py` — 路由
- [ ] `app/services/{module}.py` — 业务逻辑（如需要）
- [ ] `main.py` — 路由注册 + 模型预加载（如需要）

**文档**：
- [ ] `ai-log.md` 追加开发记录
- [ ] PR 描述说明变更内容

---

## 5. 开发工作流规范

### 5.1 Git 分支与提交

```bash
# 分支命名
feat/模块名-功能描述    # 新功能
fix/问题描述            # 修复
refactor/重构内容       # 重构

# 提交信息格式
type: 中文描述
# 示例：
feat: 添加测评结果报告页面
fix: 修复录音权限检测失败问题
```

### 5.2 AI 辅助开发流程

每次让 AI 开发新功能时，按以下步骤：

1. **需求澄清**：用 `requirements-clarity` 技能确保需求达到可执行标准
2. **制定计划**：让 AI 先出计划，确认方案后再编码
3. **小粒度提交**：一次只做一件事，每个独立功能点一个 commit
4. **AI 生成代码必须通读**：AI 写的代码不能直接提交，必须人工 review
5. **更新 ai-log.md**：编码完成后，先更新 `ai-log.md` → 再 commit
6. **PR 合入 dev**：至少 1 人 review 后合入

### 5.3 禁止事项

- ❌ 禁止 AI 自主执行 `alembic upgrade`（数据库迁移）
- ❌ 禁止 AI 自主执行 `git push --force` 等危险操作
- ❌ 禁止在代码中硬编码 API Key、密码
- ❌ 禁止将 `.env` 提交到 git
- ❌ 禁止在前端组件中直接写业务逻辑（必须通过 store 或 api 层）
- ❌ 禁止在组件中直接调 axios（必须通过 api 层）

---

## 6. AI 提示词模板

### 6.1 开发新模块

```
我在开发{模块名}模块，请按以下结构完成：

1. 后端 Schema（app/schemas/{module}.py）
2. 后端 API 路由（app/api/{module}.py）
3. 后端 Service（app/services/{module}.py）— 如需要
4. 前端 API 封装（frontend/src/api/{module}.js）
5. 前端 Pinia Store（frontend/src/stores/{module}.js）
6. 前端页面（frontend/src/views/{module}/）
7. 路由注册

请参照项目规范（docs/ai-collaboration-standards.md），先出计划再编码。
```

### 6.2 开发前端页面

```
请在{模块名}模块下开发{页面名}页面，要求：
- 使用 Composition API（<script setup>）
- 样式使用 scoped + CSS 变量
- 状态管理用 Pinia store
- API 调用通过 api/ 层
- 参考 views/assessment/ 的页面结构和样式模式
- 处理 loading / empty / error 状态
```

### 6.3 开发后端接口

```
请为{模块名}添加{接口名}接口，要求：
- 路由在 app/api/{module}.py 中
- Pydantic Schema 在 app/schemas/{module}.py 中
- 业务逻辑在 app/services/{module}.py 中
- 所有字段有 description
- 错误处理用 HTTPException，区分 422/503/500
- 文件上传注意 finally 清理临时文件
- 参考 app/api/pronunciation.py 的模式
```

---

## 附录：已有模块速查

| 模块 | 前端 | 后端 | 状态 |
|------|------|------|------|
| 1. 用户注册与画像 | Mock | 无 | ❌ Mock |
| 2. 水平智能测评 | `views/assessment/` + `stores/assessment.js` | 无 | ❌ Mock（前端硬编码题目+随机评分） |
| 4. 发音评测 | `views/pronunciation/` + `api/pronunciation.js` | `api/pronunciation.py` + `services/pronunciation.py` | ✅ 已实现 |
| 6. 智能对话 | `views/conversation/` + `api/conversation.js` | `api/conversation.py` + `services/asr.py/llm.py/tts.py` | ✅ 已实现 |
| 8. 角色扮演 | `views/roleplay/` + `api/roleplay.js` | `api/roleplay.py` + `schemas/roleplay.py` | ⏳ Schema 已定义 |

---

> **本规范随项目迭代持续更新，每次发现新的最佳实践或踩坑教训后及时补充。**