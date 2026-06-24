# test-master 使用指南

> 适用项目：Lingolab-ai 英语口语训练系统
> 安装日期：2026-06-24

---

## 一、概述

test-master 是 Claude Code 的测试技能插件，内置 12 年 QA 经验的测试架构师思维模式，覆盖功能、性能、安全三个维度。

### 三种思维模式

| 模式 | 关注点 | 示例 |
|------|--------|------|
| **[Test]** | 功能正确性 | 这个接口是否按预期返回？ |
| **[Perf]** | 性能表现 | 高并发下响应时间是否可接受？ |
| **[Security]** | 安全漏洞 | 有无注入风险？鉴权是否完善？ |

### 核心原则：TDD 铁律

| 命令类型 | 强制规则 |
|----------|----------|
| `feat`（新功能） | 必须先写测试，再写实现 |
| `fix`（Bug 修复） | 必须先写能复现问题的测试 |
| `refactor`（重构） | 必须确保现有测试全部通过 |
| `test`（纯测试） | 允许直接提交 |

---

## 二、触发方式

**上下文感知激活**，不需要手动调用。当你说的话包含以下关键词时自动激活：

`测试` `test` `单元测试` `集成测试` `E2E` `覆盖率` `性能测试` `安全测试` `回归` `测试策略` `测试框架`

### 高效触发示例

```
✅ "帮我设计认证模块的测试策略，包括单元测试和 API 集成测试"
✅ "给发音评测的评分函数写单元测试"
✅ "排查 test_auth.py 的失败原因"
✅ "这个 PR 需要补充哪些测试？"
```

### 低效触发（不推荐）

```
❌ "用 test-master 帮我写测试"       ← 不需要显式调用
❌ "写测试"                           ← 太模糊，没有指定范围
```

---

## 三、五阶段工作流

每次测试任务按以下流程执行：

```
① Define scope     → 确定测什么、不测什么
② Create strategy  → 选择测试类型和工具
③ Write tests      → 生成测试代码
④ Execute          → 运行并收集结果
⑤ Report           → 输出报告到 test-reports/
```

---

## 四、测试单位

**以模块为单位**，一个模块包含三层测试：

```
模块（如 认证模块）
├── 单元测试    → Schema 校验、工具函数、纯逻辑
├── 集成测试    → API 端点、数据库读写、服务间调用
└── E2E 测试    → 用户完整流程
```

### 项目模块清单

| # | 模块 | 优先级 | 测试状态 |
|---|------|--------|----------|
| 1 | 用户注册与多维度画像 | 🔴 高 | 部分（Schema 已测） |
| 2 | 英语水平智能测评 | 🟡 中 | 未开始 |
| 3 | 个性化学习路径规划 | 🟢 低 | 未开始 |
| 4 | AI 发音评测与纠错 | 🔴 高 | 未开始 |
| 5 | 流利度与完整性评估 | 🟡 中 | 未开始 |
| 6 | 智能语音对话练习 | 🔴 高 | 未开始 |
| 7 | AI 语法纠错与润色 | 🟡 中 | 未开始 |
| 8 | 情景角色扮演 | 🟡 中 | 未开始 |
| 9-16 | 其余模块 | 🟢 低 | 未开始 |

---

## 五、测试框架

| 端 | 框架 | 配置文件 | 运行命令 |
|----|------|----------|----------|
| 后端 | pytest 9.1.1 | `backend/pytest.ini` | `python -m pytest` |
| 前端 | vitest 4.1.9 | `frontend/vite.config.js` (test 块) | `npm run test` |

### 后端测试文件命名

```
backend/
├── test_auth.py              # 认证模块
├── test_pronunciation.py     # 发音评测
├── test_conversation.py      # 智能对话
├── test_roleplay.py          # 角色扮演
└── ...
```

### 前端测试文件命名

```
frontend/src/
├── api/__tests__/            # API 层测试
├── stores/__tests__/         # Pinia Store 测试
├── components/__tests__/     # 组件测试
└── views/__tests__/          # 页面测试
```

---

## 六、报告留存

所有测试报告存放在 `test-reports/` 目录，命名规范：

```
test-reports/
└── YYYY-MM-DD-模块名.md
```

### 报告模板包含

- **Summary** — 通过/失败/跳过/耗时
- **Test Cases** — 每条用例及结果
- **Findings** — 按 CRITICAL/HIGH/MEDIUM/LOW 分级
- **Coverage Gaps** — 未覆盖的代码路径
- **Recommendations** — 优先级排序的改进建议

### 严重等级定义

| 等级 | 标准 |
|------|------|
| **CRITICAL** | 安全漏洞、数据丢失、系统崩溃 |
| **HIGH** | 核心功能损坏、严重性能问题 |
| **MEDIUM** | 功能部分可用、有临时方案 |
| **LOW** | 小问题、边缘情况、样式问题 |

---

## 七、最佳实践

### 必须遵守
- 每个测试覆盖正常路径 **AND** 错误/边界情况
- Mock 外部依赖（数据库、API），不在单元测试中调真实服务
- 每个测试独立运行，不依赖执行顺序
- 断言具体值（`assert result == 90`），不断言 truthy/falsy

### 禁止事项
- 跳过错误路径测试（不要只测 try 的成功分支）
- 在测试中使用生产数据（用 fixtures 或 factories）
- 创建有顺序依赖的测试
- 忽略 flaky 测试（隔离并修复，不要反复重跑等通过）
- 测试实现细节（内部方法调用），应测试可观测行为

### 测试用例模板

**pytest（后端）**：
```python
def test_register_username_too_short(self):
    """用户名少于 4 字符 → 抛出 ValueError"""
    with pytest.raises(ValueError, match="用户名需 4-20 个字符"):
        RegisterRequest(
            username="abc",
            email="test@example.com",
            password="pass1234",
            age=20,
            learning_goal="daily",
        )
```

**vitest（前端）**：
```js
describe('calculateDiscount', () => {
  it('applies 10% discount for premium users', () => {
    const result = calculateDiscount({ price: 100, userTier: 'premium' });
    expect(result).toBe(90);
  });

  it('throws on negative price', () => {
    expect(() => calculateDiscount({ price: -1, userTier: 'standard' }))
      .toThrow('Price must be non-negative');
  });
});
```

---

## 八、参考文档

test-master 内置 10 份专业参考文档，按需自动加载，无需手动查阅：

| 文档 | 内容 | 触发场景 |
|------|------|----------|
| `unit-testing.md` | Jest/Vitest/pytest 模式 | 写单元测试 |
| `integration-testing.md` | API 测试、Supertest | 写集成测试 |
| `e2e-testing.md` | E2E 策略、用户流程 | 写端到端测试 |
| `performance-testing.md` | k6 负载测试 | 性能测试 |
| `security-testing.md` | OWASP 安全清单 | 安全测试 |
| `tdd-iron-laws.md` | TDD 方法论 | 新功能开发 |
| `testing-anti-patterns.md` | 测试反模式 | 代码审查 |
| `test-reports.md` | 报告模板 | 生成报告 |
| `qa-methodology.md` | QA 方法论 | 测试策略 |
| `automation-frameworks.md` | 自动化框架 | CI/CD 集成 |

---

## 九、协同 Skills

当前保留的 5 个测试相关 skills 可协同工作：

| Skill | 协同场景 |
|-------|----------|
| `test-master` | 写测试、定策略、出报告 |
| `playwright-expert` | 浏览器端 E2E 测试（登录流程、页面交互） |
| `code-reviewer` | 审查测试代码质量、发现反模式 |
| `debugging-wizard` | 排查测试失败、修复 flaky test |
| `security-reviewer` | 安全测试（注入、鉴权、敏感信息泄露） |

---

## 十、常用场景速查

| 场景 | 你说的话 |
|------|----------|
| 给新模块写测试 | "帮我设计发音评测模块的测试策略" |
| 补充单元测试 | "给 pronunciation.py 的评分函数写单元测试" |
| 测试 API 接口 | "写对话接口的集成测试，覆盖正常和异常情况" |
| 跑回归测试 | "跑一下认证模块的全部测试" |
| 排查失败 | "test_auth.py 有 3 个失败，帮我排查原因" |
| 补充测试 | "这个 PR 改了 auth 模块，需要补充哪些测试？" |
| 性能测试 | "给对话接口做性能测试，模拟 100 并发" |
| 安全审查 | "审查认证接口的安全漏洞" |
| 生成报告 | "跑完测试后生成报告并存到 test-reports/" |
| 前端组件测试 | "给 LoginView.vue 写组件测试" |