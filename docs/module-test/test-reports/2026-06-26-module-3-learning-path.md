# 模块 3：个性化学习路径规划 — 测试报告

> 测试日期：2026-06-26
> 测试分支：feat/module-3-test
> 测试文件：backend/test_learning_path.py

---

## 一、测试范围

| 类别 | 测试类 | 用例数 | 说明 |
|------|--------|--------|------|
| 知识图谱 | TestKnowledgeGraph | 7 | 图构建/BFS前置链/拓扑排序/CEFR筛选/资料匹配/最短路径 |
| 推荐算法 | TestLevelMatch | 5 | CEFR 等级匹配：同级/差1级/差2级/差3级+/无效值 |
| 推荐算法 | TestInterestMatch | 6 | 兴趣标签匹配：无数据/无交集/部分/完全 |
| 推荐算法 | TestWeaknessMatch | 4 | 短板匹配：无技能/无交集/部分/完全 |
| 推荐算法 | TestNovelty | 6 | 新颖度：首次/disliked/1次/2次/3次/多次钳制 |
| 推荐算法 | TestCompositeScore | 3 | 四因子综合：满分/disliked归零/推荐打折 |
| 推荐算法 | TestAdjustDifficulty | 6 | CEFR 难度调整：升降/边界/无效/完整循环 |
| Schema | TestTaskItemSchema | 3 | 任务项 Schema |
| Schema | TestDailyTasksResponseSchema | 1 | 每日任务响应 |
| Schema | TestAdjustDifficultyRequestSchema | 2 | 调整难度请求 |
| Schema | TestMaterialItemSchema | 1 | 资料推荐项 |
| Schema | TestRecommendationsResponseSchema | 1 | 资料推荐响应 |
| Schema | TestHistoryDaySchema | 1 | 历史记录 |

**合计：13 个测试类，46 个用例**

---

## 二、测试结果

```
46 passed in 0.09s
```

| 指标 | 值 |
|------|-----|
| 总用例数 | 46 |
| 通过 | 46 |
| 失败 | 0 |
| 执行时间 | 0.09s |

---

## 三、关键算法覆盖详情

### 3.1 知识图谱图遍历

| 测试 | 说明 |
|------|------|
| test_graph_node_count | 16 节点（6 CEFR + 5 技能 + 3 资料 + 2 场景） |
| test_graph_edge_count | 12 边（5 BELONGS_TO + 2 HAS_PREREQ + 4 TEACHES + 1 COVERS） |
| test_prerequisite_chain | conditionals→present_perfect→past_tense 拓扑排序正确 |
| test_get_skills_by_cefr | A1 等级筛选出 th_sound + vowels |
| test_get_materials_teaching_skill | th_sound 被 video_1 + audio_1 教授 |
| test_shortest_path | conditionals→present_perfect→past_tense 最短路径 |

### 3.2 四因子推荐评分

| 测试 | 弱点 | 等级 | 兴趣 | 新颖度 | 综合分 |
|------|------|------|------|--------|--------|
| test_perfect_match | 1.0 | 1.0 | 1.0 | 1.0 | 100.0 |
| test_disliked_score_zero | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 |
| test_recent_dampened | 1.0 | 1.0 | 1.0 | 0.7 | 70.0 |

### 3.3 CEFR 难度调整

| 测试 | 当前 | 方向 | 结果 |
|------|------|------|------|
| test_harder_from_b1 | B1 | harder | B2 |
| test_easier_from_b1 | B1 | easier | A2 |
| test_harder_at_c2 | C2 | harder | None |
| test_easier_at_a1 | A1 | easier | None |
| test_full_cycle | A1→C2→A1 | 循环 | 全部正确 |

---

## 四、测试局限性

| 未覆盖项 | 原因 |
|----------|------|
| 六步任务生成完整流程 | 依赖 DB + 知识图谱单例加载 |
| 任务操作（skip/replace/complete） | 依赖 DB 写入 |
| 资料推荐端到端 | 依赖 DB + kg_service |
| 前端组件 | 需要浏览器环境 |

---

## 五、结论

**46/46 用例全部通过**，学习路径模块的知识图谱图遍历算法（BFS + 拓扑排序）、四因子推荐评分、CEFR 难度调整、Schema 校验均逻辑正确。
