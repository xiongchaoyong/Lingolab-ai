# 模块 2：英语水平智能测评 — 测试报告

> 测试日期：2026-06-26
> 测试分支：feat/module-2-test
> 测试文件：backend/test_assessment.py

---

## 一、测试范围

| 类别 | 测试类 | 用例数 | 说明 |
|------|--------|--------|------|
| Schema 校验 | TestQuestionItem | 4 | 题目 Schema：必填字段、默认值、类型枚举 |
| Schema 校验 | TestAssessmentStartResponse | 1 | 开始测评响应结构 |
| Schema 校验 | TestAssessmentAnswerResponse | 2 | 逐题提交响应：未完成/已完成两种状态 |
| Schema 校验 | TestCEFRLevel | 1 | CEFR 等级 Schema（A1-C2 六级） |
| Schema 校验 | TestAssessmentSubmitResponse | 1 | 测评结果响应：综合分+四维+短板 |
| 核心算法 | TestGetCEFR | 13 | CEFR 定级算法：6 个阈值 + 5 个边界 + 满分/零分 |
| 核心算法 | TestLevelToCEFR | 10 | 数值等级→CEFR 转换：6 个级别 + 四舍五入 + 钳制 |
| 核心算法 | TestAdjustLevel | 9 | 自适应难度调整：升降 + 钳制 + 连续/交替行为 |
| 核心算法 | TestCEFRMapping | 3 | CEFR 数值映射表完整性 |

**合计：9 个测试类，44 个用例**

---

## 二、测试结果

```
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1
collected 44 items

test_assessment.py::TestQuestionItem::test_valid_question PASSED
test_assessment.py::TestQuestionItem::test_options_default_empty PASSED
test_assessment.py::TestQuestionItem::test_options_for_multiple_choice PASSED
test_assessment.py::TestQuestionItem::test_all_types_accepted PASSED
test_assessment.py::TestAssessmentStartResponse::test_valid_response PASSED
test_assessment.py::TestAssessmentAnswerResponse::test_not_complete_with_next_question PASSED
test_assessment.py::TestAssessmentAnswerResponse::test_complete_without_next_question PASSED
test_assessment.py::TestCEFRLevel::test_all_levels PASSED
test_assessment.py::TestAssessmentSubmitResponse::test_valid_response PASSED
test_assessment.py::TestGetCEFR::test_c2_threshold PASSED
test_assessment.py::TestGetCEFR::test_c1_threshold PASSED
test_assessment.py::TestGetCEFR::test_b2_threshold PASSED
test_assessment.py::TestGetCEFR::test_b1_threshold PASSED
test_assessment.py::TestGetCEFR::test_a2_threshold PASSED
test_assessment.py::TestGetCEFR::test_a1_threshold PASSED
test_assessment.py::TestGetCEFR::test_boundary_95_is_c1 PASSED
test_assessment.py::TestGetCEFR::test_boundary_80_is_b2 PASSED
test_assessment.py::TestGetCEFR::test_boundary_60_is_b1 PASSED
test_assessment.py::TestGetCEFR::test_boundary_40_is_a2 PASSED
test_assessment.py::TestGetCEFR::test_boundary_20_is_a1 PASSED
test_assessment.py::TestGetCEFR::test_perfect_score PASSED
test_assessment.py::TestGetCEFR::test_zero_score PASSED
test_assessment.py::TestLevelToCEFR::test_a1 PASSED
test_assessment.py::TestLevelToCEFR::test_a2 PASSED
test_assessment.py::TestLevelToCEFR::test_b1 PASSED
test_assessment.py::TestLevelToCEFR::test_b2 PASSED
test_assessment.py::TestLevelToCEFR::test_c1 PASSED
test_assessment.py::TestLevelToCEFR::test_c2 PASSED
test_assessment.py::TestLevelToCEFR::test_round_up PASSED
test_assessment.py::TestLevelToCEFR::test_round_down PASSED
test_assessment.py::TestLevelToCEFR::test_clamp_below_1 PASSED
test_assessment.py::TestLevelToCEFR::test_clamp_above_6 PASSED
test_assessment.py::TestAdjustLevel::test_score_60_increases PASSED
test_assessment.py::TestAdjustLevel::test_score_below_60_decreases PASSED
test_assessment.py::TestAdjustLevel::test_score_100_increases PASSED
test_assessment.py::TestAdjustLevel::test_score_0_decreases PASSED
test_assessment.py::TestAdjustLevel::test_clamp_at_max_6 PASSED
test_assessment.py::TestAdjustLevel::test_clamp_at_min_1 PASSED
test_assessment.py::TestAdjustLevel::test_repeated_correct_raises_to_c2 PASSED
test_assessment.py::TestAdjustLevel::test_repeated_wrong_drops_to_a1 PASSED
test_assessment.py::TestAdjustLevel::test_alternating_stays_middle PASSED
test_assessment.py::TestCEFRMapping::test_all_6_levels_exist PASSED
test_assessment.py::TestCEFRMapping::test_values_are_sequential PASSED
test_assessment.py::TestCEFRMapping::test_bidirectional_mapping PASSED

============================== 44 passed in 0.08s ==============================
```

| 指标 | 值 |
|------|-----|
| 总用例数 | 44 |
| 通过 | 44 |
| 失败 | 0 |
| 错误 | 0 |
| 执行时间 | 0.08s |

---

## 三、关键算法覆盖详情

### 3.1 CEFR 定级算法 `_get_cefr(score)`

| 测试 | 分值 | 期望等级 | 说明 |
|------|------|----------|------|
| test_c2_threshold | 96 | C2 | 上界阈值 |
| test_c1_threshold | 81 | C1 | 上界阈值 |
| test_b2_threshold | 61 | B2 | 上界阈值 |
| test_b1_threshold | 41 | B1 | 上界阈值 |
| test_a2_threshold | 21 | A2 | 上界阈值 |
| test_a1_threshold | 0 | A1 | 下界 |
| test_boundary_95_is_c1 | 95 | C1 | 边界：低于 C2 阈值 |
| test_boundary_80_is_b2 | 80 | B2 | 边界：低于 C1 阈值 |
| test_boundary_60_is_b1 | 60 | B1 | 边界：低于 B2 阈值 |
| test_boundary_40_is_a2 | 40 | A2 | 边界：低于 B1 阈值 |
| test_boundary_20_is_a1 | 20 | A1 | 边界：低于 A2 阈值 |
| test_perfect_score | 100 | C2 | 满分 |
| test_zero_score | 0 | A1 | 零分 |

### 3.2 自适应难度调整 `_adjust_level(current, score)`

| 测试 | 当前等级 | 得分 | 期望结果 | 说明 |
|------|----------|------|----------|------|
| test_score_60_increases | 3.0 | 60 | 3.5 | 答对升级 |
| test_score_below_60_decreases | 3.0 | 59 | 2.5 | 答错降级 |
| test_clamp_at_max_6 | 6.0 | 100 | 6.0 | C2 不再升 |
| test_clamp_at_min_1 | 1.0 | 0 | 1.0 | A1 不再降 |
| test_repeated_correct | 1.0→6.0 | 连续100 | 6.0 | A1→C2 需 10 次 |
| test_repeated_wrong | 6.0→1.0 | 连续0 | 1.0 | C2→A1 需 10 次 |
| test_alternating | 3.0 | 交替 | 3.0 | 对称回原位 |

---

## 四、测试局限性

本次测试仅覆盖 **Schema 校验 + 纯函数算法**，未涉及：

| 未覆盖项 | 原因 |
|----------|------|
| API 端点集成测试 | 需要数据库连接 + 测试客户端 |
| 题库随机抽取逻辑 | 依赖 DB 查询 |
| 口语题 ASR + LLM 评分 | 依赖 WhisperX + DashScope 服务 |
| 会话管理（开始/恢复） | 依赖内存字典 + DB 双写 |
| 全对/全错追加题 | 依赖端到端答题流程 |

---

## 五、结论

**44/44 用例全部通过**，测评模块的 Schema 定义和核心算法（CEFR 定级、等级转换、自适应难度调整）逻辑正确、边界处理完备。
