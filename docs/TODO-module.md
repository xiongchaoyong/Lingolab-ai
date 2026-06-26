# 模块完成度 TODO 清单

> 基于需求说明书与实际代码对比分析，生成于 2026-06-26

---

## 一、数据库模型缺失（最大短板）

需求说明书定义了 30 张表，当前仅实现约 7 张，缺失 21 张表的 ORM 模型：

| # | 缺失表名 | 所属模块 | 优先级 |
|---|----------|----------|--------|
| 1 | `pronunciation_records` | 发音评测 | P0 |
| 2 | `conversation_sessions` | 智能对话 | P0 |
| 3 | `conversation_messages` | 智能对话 | P0 |
| 4 | `daily_tasks` | 学习路径 | P0 |
| 5 | `learning_materials` | 资料推荐 | P1 |
| 6 | `material_records` | 资料推荐 | P1 |
| 7 | `user_scores` | 游戏化激励 | P1 |
| 8 | `user_badges` | 游戏化激励 | P1 |
| 9 | `dubbing_content` | 配音挑战 | P1 |
| 10 | `dubbing_records` | 配音挑战 | P1 |
| 11 | `learning_predictions` | 效果预测 | P1 |
| 12 | `notices` | 预警通知 | P1 |
| 13 | `challenge_topics` | 语音挑战 | P2 |
| 14 | `challenge_records` | 语音挑战 | P2 |
| 15 | `discussion_topics` | 话题讨论 | P2 |
| 16 | `discussion_comments` | 话题讨论 | P2 |
| 17 | `groups` | 学习小组 | P2 |
| 18 | `group_members` | 学习小组 | P2 |
| 19 | `faq_entries` | 智能客服 | P1 |
| 20 | `support_sessions` | 智能客服 | P1 |
| 21 | `security_logs` | 安全日志 | P2 |

**额外待办**：
- [ ] 初始化 Alembic 迁移框架
- [ ] 编写初始迁移文件，创建全部 30 张表
- [ ] 迁移文件人工审查后执行 `alembic upgrade`

---

## 二、后端 API 缺失

以下模块前端有页面，但后端无独立 API 路由：

| # | 模块 | 对应前端页面 | 需新建后端文件 | 优先级 |
|---|------|-------------|---------------|--------|
| 1 | 游戏化闯关/配音挑战 | `views/gamification/ChallengeView.vue` | `api/gamification.py` + `services/gamification.py` + `schemas/gamification.py` | P1 |
| 2 | 学习进度可视化 | `views/progress/ProgressView.vue` | `api/progress.py` + `services/progress.py` + `schemas/progress.py` | P1 |
| 3 | 效果预测与预警 | 无页面 | `api/prediction.py` + `services/prediction.py` + `schemas/prediction.py` + 前端页面 | P1 |
| 4 | 语音挑战广场 | `views/community/CommunityView.vue` | `api/community.py` + `services/community.py` + `schemas/community.py` | P2 |
| 5 | 话题讨论区 | 合并在 CommunityView | 同上 | P2 |
| 6 | 学习小组 | 合并在 CommunityView | 同上 | P2 |

---

## 三、前端页面需完善（壳页面 → 真实对接）

以下页面已有 UI 框架，但大概率使用 mock 数据或静态内容，需要对接真实 API：

| # | 页面 | 行数 | 待办 |
|---|------|------|------|
| 1 | `community/CommunityView.vue` | 225 | 对接社区 API（挑战/讨论/小组） |
| 2 | `gamification/ChallengeView.vue` | 233 | 对接闯关/配音 API + 积分勋章 |
| 3 | `progress/ProgressView.vue` | 308 | 对接进度 API + ECharts 雷达图/折线图/热力图 |
| 4 | `admin/DashboardView.vue` | 132 | 对接仪表盘 API + 8 项指标 + CEFR 饼图 |
| 5 | `admin/ContentManageView.vue` | 100 | 对接内容 CRUD API（题库/跟读/资料/配音/FAQ） |
| 6 | `teacher/StudentReportView.vue` | 81 | 对接学生报告 API + 录音回放 + 教师点评 |
| 7 | `admin/FeedbackView.vue` | — | 需确认功能定位，可能需对接 support_sessions |

---

## 四、功能模块逐项 TODO

### 模块 1：用户服务（完成度 80%）
- [ ] 补充 `user_profiles` 的 Alembic 迁移
- [ ] 完善 JWT 刷新 Token 机制（当前仅 24h 有效期，无刷新）
- [ ] 账号禁用/恢复功能对接 `is_active` 字段

### 模块 2：英语水平测评（完成度 60%）
- [ ] 测评题目从数据库加载（当前可能硬编码）
- [ ] 实现自适应难度调整（答对 +0.5 级、答错 -0.5 级）
- [ ] 口语题接入 Whisper 转写 + LLM 四维评分
- [ ] 全对追加 C2 确认题、全错追加 A1 兜底题
- [ ] 测评中途退出恢复机制
- [ ] 30 天重测评限制

### 模块 3：发音评测与纠错（完成度 70%）
- [ ] 建立 `pronunciation_records` 表模型
- [ ] 发音评测结果持久化到数据库
- [ ] 跟读内容库 `pronunciation_content` 表 + CRUD
- [ ] 单词模式 vs 句子模式权重区分
- [ ] IPA 音标展示

### 模块 4：智能语音对话（完成度 65%）
- [ ] 建立 `conversation_sessions` + `conversation_messages` 表模型
- [ ] 对话会话和消息持久化
- [ ] 10 轮上下文记忆（当前实现程度待确认）
- [ ] 难度自适应（A1-A2 基础 / B1 中阶 / B2+ 高阶）
- [ ] 4 个 MVP 场景完善（自我介绍/问路/购物/餐厅）
- [ ] 对话结束四维评分（发音 30% + 语法 30% + 词汇 20% + 参与度 20%）

### 模块 5：流利度与完整性评估（完成度 40%）
- [ ] 五维流利度计算（语速/停顿/重复/语法/相关性）
- [ ] 静默评分嵌入对话每轮
- [ ] 对话结束汇总流利度报告
- [ ] 流利度数据持久化到 `conversation_messages.fluency_scores`

### 模块 6：语法纠错与润色（完成度 60%）
- [ ] 6 类语法错误检测（时态/主谓一致/冠词/介词/词序/单复数）
- [ ] 错误高亮展示 + 修正版 + 语法说明
- [ ] 润色建议（礼貌升级/口语化/俚语/缩略/精简）
- [ ] 纠错结果持久化到 `conversation_messages.grammar_check`
- [ ] 常见错误 Top 3 汇总

### 模块 7：角色扮演（完成度 65%）
- [ ] 角色说明卡（角色目标/常见用语/建议话术）
- [ ] 角色 Prompt 注入（面试者/服务员/导游）
- [ ] 四维角色评分（贴合度 40% + 礼仪 25% + 术语 20% + 应对 15%）
- [ ] 对话结果持久化

### 模块 8：学习路径规划（完成度 50%）
- [ ] 建立 `daily_tasks` 表模型
- [ ] 规则引擎六步法实现（短板优先→目标加权→CEFR→年龄→兴趣→输出）
- [ ] 每日任务持久化
- [ ] 用户操作：跳过/换一个/调整难度/加量
- [ ] 每日首次登录自动生成，手动刷新限 3 次

### 模块 9：学习资料推荐（完成度 50%）
- [ ] 建立 `learning_materials` + `material_records` 表模型
- [ ] 三因子评分算法（短板 40% + 难度 35% + 兴趣 25%）
- [ ] 每次展示 6 条（视频×2 + 文章×2 + 音频×2）
- [ ] 7 天内不重复推荐
- [ ] "不感兴趣"反馈记录

### 模块 10：游戏化闯关学习（完成度 25%）
- [ ] 新建后端 API `gamification.py`
- [ ] 5 关难度递增（A1→B2），每关发音分 ≥70 通过
- [ ] 配音挑战：原声播放→用户配音→三维评估（发音 50% + 语调 30% + 情感 20%）
- [ ] 积分系统（每日任务 +10/项、闯关全通 +130、配音 +30 等）
- [ ] 7 种勋章体系（新手上路/坚持之星/发音突破等）
- [ ] 前端对接真实 API

### 模块 11：学习进度可视化（完成度 30%）
- [ ] 新建后端 API `progress.py`
- [ ] 雷达图（五维 + 前后对比）
- [ ] 趋势折线图（发音蓝 + 流利度绿）
- [ ] 日历热力图（4 色 GitHub 风格）
- [ ] 6 项核心统计（累计时长/打卡/连续打卡/最长连续/跟读/对话）
- [ ] 日/周/月/全部时间范围切换
- [ ] 前端接入 ECharts 渲染真实数据

### 模块 12：效果预测与预警（完成度 0%）
- [ ] 新建后端 API `prediction.py` + Service + Schema
- [ ] 新建前端页面 `views/prediction/PredictionView.vue`
- [ ] 线性回归预测达标时间（最近 30 天综合分）
- [ ] 3 条预警规则（连续 3 天未学/时长降 >50%/发音 7 天未提升）
- [ ] 建立 `learning_predictions` + `notices` 表模型
- [ ] 预警消息推送

### 模块 13-15：社区服务（完成度 15%）
- [ ] 新建后端 API `community.py` + Service + Schema
- [ ] **语音挑战广场**：发起挑战→参与跟读→发音评分排名→7 天归档
- [ ] **话题讨论区**：英文评论→语法纠错→错误标红高亮
- [ ] **学习小组**：创建/加入（上限 20 人）→打卡→互评→周排名→30 天无活动归档
- [ ] 建立 6 张表模型（`challenge_topics` / `challenge_records` / `discussion_topics` / `discussion_comments` / `groups` / `group_members`）
- [ ] 前端社区页面对接真实 API

### 模块 16-17：教师端管理（完成度 70%）
- [ ] 教师点评录音功能完善（`pronunciation_records.teacher_review`）
- [ ] 学生报告页面完善（雷达图 + 趋势图 + 录音回放）
- [ ] 邀请码 24h 过期刷新机制
- [ ] 完成率自动计算

### 模块 18-19：运营管理后台（完成度 50%）
- [ ] 数据仪表盘 8 项指标真实查询（DAU/MAU/留存率/总时长/人均时长/对话完成率/日新增）
- [ ] CEFR 饼图 + 新增趋势折线图
- [ ] 内容管理 CRUD 完善（题库/跟读/资料/配音/FAQ）
- [ ] 30 天以上数据缓存
- [ ] 操作日志记录完善

### 模块 20-21：智能客服（完成度 55%）
- [ ] 建立 `faq_entries` + `support_sessions` + `security_logs` 表模型
- [ ] 10 个 FAQ 预设条目入库
- [ ] 问题自动分类（产品使用/学习建议/技术故障/退款付费/闲聊）
- [ ] 超范围固定话术拒绝
- [ ] 连续 3 次相同问题引导人工
- [ ] Deepseek 故障降级 FAQ 纯展示
- [ ] 语音输入转文字提问

---

## 五、基础设施待办

- [ ] Alembic 初始化 + 迁移文件编写
- [ ] 数据库 seed 数据脚本（测评题库/跟读内容/FAQ/配音片段等）
- [ ] 前端全局 loading / error 状态统一处理
- [ ] WebSocket 端点（需求说明书提到 `/ws`，当前未实现）
- [ ] 文件上传目录 `uploads/` 管理 + 过期清理
- [ ] 性能优化：AI/ML 推理结果缓存
- [ ] 浏览器兼容性测试（Chrome 90+ / Edge 90+ / Firefox 88+）
