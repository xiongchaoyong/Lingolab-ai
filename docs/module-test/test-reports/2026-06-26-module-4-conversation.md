# 模块 4：智能语音对话练习 — 测试报告

> 测试日期：2026-06-26
> 测试分支：feat/module-4-test
> 测试文件：backend/test_conversation.py

---

## 一、测试范围

| 类别 | 测试类 | 用例数 | 说明 |
|------|--------|--------|------|
| 流利度算法 | TestGetFluencyGrade | 9 | 分段评级：5 级 + 4 个边界值 |
| 流利度算法 | TestCountWords | 6 | 单词计数：正常/单/空/空白/多余空格/换行 |
| 流利度算法 | TestDetectRepetitions | 6 | 重复检测：无重复/短文本/连续重复/全重复 |
| 流利度算法 | TestAssessAlgorithmic | 7 | 算法流利度：理想语速/慢速/快速/多停顿/无词兜底/结构/满分 |
| 流利度算法 | TestAggregateFluency | 6 | 多轮汇总：空/单轮/多轮/最佳轮次/维度平均/评级映射 |
| Schema | TestConversationStartRequest | 2 | 开始请求：默认值/自定义值 |
| Schema | TestConversationStartResponse | 1 | 开始响应 |
| Schema | TestConversationSpeakResponse | 3 | 说话响应：基础/语法纠错/完成标记 |
| Schema | TestConversationEndResponse | 3 | 结束响应：基础/流利度/默认空列表 |

**合计：9 个测试类，43 个用例**

---

## 二、测试结果

```
43 passed in 0.07s
```

| 指标 | 值 |
|------|-----|
| 总用例数 | 43 |
| 通过 | 43 |
| 失败 | 0 |
| 执行时间 | 0.07s |

---

## 三、关键算法覆盖详情

### 3.1 流利度评级 `_get_fluency_grade(score)`

| 分值范围 | 评级 | 测试覆盖 |
|----------|------|----------|
| 85-100 | 优秀 | ✅ 边界 85 |
| 70-84 | 良好 | ✅ 边界 70/84 |
| 55-69 | 中等 | ✅ 边界 55/69 |
| 40-54 | 初级 | ✅ 边界 40/54 |
| 0-39 | 入门 | ✅ 边界 0/39 |

### 3.2 算法流利度 `assess_algorithmic()`

| 测试 | 语速 | 停顿 | 重复 | 满分 |
|------|------|------|------|------|
| test_ideal_speech | 25/25 | 20/20 | 20/20 | 65/65 |
| test_slow_speech | <25 | - | - | - |
| test_fast_speech | <25 | - | - | - |
| test_many_pauses | - | <20 | - | - |
| test_overall_max_65 | - | - | - | ≤65 |

### 3.3 多轮汇总 `aggregate_fluency()`

| 测试 | 轮次 | 综合分 | 评级 | 最佳轮 |
|------|------|--------|------|--------|
| test_empty | 0 | 0 | 入门 | None |
| test_single | 1 | 57 | 中等 | 1 |
| test_multiple | 2 | 84 | 良好 | 2 |
| test_best_round | 3 | - | - | 2 |

---

## 四、测试局限性

| 未覆盖项 | 原因 |
|----------|------|
| API 端点（/start, /speak, /end） | 依赖 ASR + LLM + TTS 服务 |
| SSE 流式对话 | 需要异步 StreamingResponse 测试客户端 |
| TTS 预取缓存 | 依赖 Edge TTS 服务 |
| DB 持久化 | 依赖 MySQL 连接 |

---

## 五、结论

**43/43 用例全部通过**，对话模块的流利度五维算法（语速/停顿/重复 + 评级/汇总）和 Schema 校验均逻辑正确。
