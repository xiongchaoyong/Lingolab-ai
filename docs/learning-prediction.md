# 学习预测

> 模块编号：13 — 学习效果预测与预警

---

## 功能概述

根据用户历史学习数据，通过**线性回归**预测学习趋势、预计达标时间，并结合**三条预警规则**在学习懈怠或退步时自动提醒用户。

## 数据来源

| 数据 | 来源 |
|------|------|
| 综合分 | `user_skill_scores` 表，最近 30 天每日得分 |
| 综合分公式 | 发音×0.4 + 流利度×0.3 + 语法×0.3（取每日均值） |
| 维度分 | `user_skill_scores`，按 `dimension` 字段区分（pronunciation / fluency / grammar / vocabulary） |

## 预测算法

### 线性回归（最小二乘法）

对最近 30 天的每日综合分拟合一条直线：**y = slope × day + intercept**

```
斜率 slope = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)
```

### 输出

| 字段 | 说明 |
|------|------|
| current_score | 最新一天的日均综合分 |
| trend_slope | 斜率，正值=上升，负值=下降 |
| trend | 趋势方向：`up`（斜率>0.05）/ `down`（斜率<−0.05）/ `stable` |
| target_score | 用户目标分数，默认 85，可自定义 |
| predicted_days | 按当前斜率到达目标分数所需天数 |
| predicted_date | 预计达标日期 |

### 边界处理

- 数据点 < 3 天：返回 `trend: stable`，提示数据不足
- 斜率为 0：不显示预计达标时间
- 预计天数 > 365：提示「目标较远，建议拆分小里程碑」
- 下降趋势：提示「建议增加学习时长和练习频率」

## 三条预警规则

| 规则 | 触发条件 | 判断逻辑 |
|------|----------|----------|
| 连续未学习 | `level: warning` | 最近活动日期距今 ≥ 3 天 |
| 学习时长下降 | `level: warning` | 本周活动次数 < 上周 × 50% |
| 发音停滞 | `level: info` | 最近 7 天后半段发音维度均值 ≤ 前半段 |

每条规则未触发时也返回 `info` 级别的正常消息，方便前端展示。

---

## 前后端协作

```
ProgressView.vue (学习报告页)
  ├─ useProgressStore.fetchAll()     → GET /api/progress/trend    → 趋势折线图
  └─ usePredictionStore
       ├─ fetchPrediction()           → GET /api/prediction/current → 预测卡片
       ├─ checkAlerts()               → GET /api/prediction/alerts  → 预警提醒
       └─ updateTarget(score)         → PUT /api/prediction/target  → 修改目标分
```

## 持久化

预测结果每次计算后写入 `learning_predictions` 表（upsert），字段包括 `current_score`、`trend_slope`、`target_score`、`predicted_days`、`predicted_date`。

---

## 局限性

1. **线性假设**：学习曲线通常不是线性的，初期进步快、后期趋于平缓，线性回归会低估后期达标时间
2. **数据粒度粗**：综合分是对全部维度取均值，丢失了维度间的差异信息
3. **样本量小**：30 天窗口内若学习频率低，数据点稀疏会导致预测不稳定
4. **无外部因素**：不考虑难度提升、内容变化等影响
