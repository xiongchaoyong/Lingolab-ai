# 模块完成度 TODO 清单

> 基于需求说明书与实际代码对比分析，更新于 2026-06-26
>
> **当前状态：21 个功能模块全部实现闭环（DB 模型 → API → 前端）**

---

## 一、总览

| 维度 | 数量 | 状态 |
|------|------|------|
| 数据库表 | 32 张 | ✅ 全部建表（init.sql + Alembic 迁移） |
| ORM 模型文件 | 12 个 | ✅ 全部实现 |
| API 路由 | 14 个 | ✅ 全部注册到 main.py |
| Service 服务 | 15 个 | ✅ 全部实现 |
| Schema 定义 | 15 个 | ✅ 全部实现 |
| 前端页面 | 25 个 | ✅ 全部对接真实 API |

---

## 二、各模块完成情况

### 模块 1：用户注册与多维度画像 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| JWT 注册/登录 | ✅ | `api/auth.py`，bcrypt 密码哈希 |
| 个人资料 CRUD | ✅ | `api/auth.py` + `ProfileView.vue` |
| 多维画像（年龄/目标/水平） | ✅ | `user_profiles` 表 |
| JWT 刷新 Token | ✅ | `POST /auth/refresh`，前端自动续期 |
| 账号禁用/恢复 | ✅ | `PUT /auth/status`，管理员操作 |

### 模块 2：英语水平智能测评 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 题库 30 题（DB 加载） | ✅ | `assessment_questions` 表 + seed 脚本 |
| 自适应难度调整 | ✅ | CEFR 数值映射 A1-C2: 1.0-6.0，得分≥60 升 0.5 级 |
| 口语题 ASR + LLM 四维评分 | ✅ | WhisperX 转写 + qwen-plus 评分 |
| 全对/全错追加题 | ✅ | 全对→C2 确认题，全错→A1 基础题 |
| 30 天重测评限制 | ✅ | `last_assessment_at` 字段检查 |
| 会话持久化 + 退出恢复 | ✅ | `POST /restore` 端点 + localStorage 同步 |
| CEFR 定级 + 短板分析 | ✅ | 四维均分→CEFR + 弱项提示 |

### 模块 3：个性化学习路径规划 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 知识图谱（129 节点 + 292 边） | ✅ | `kg_nodes` + `kg_edges` 表 |
| NetworkX BFS/拓扑排序 | ✅ | `KnowledgeGraphService` |
| 规则引擎六步法 | ✅ | 短板优先→目标加权→CEFR→年龄→兴趣→输出 |
| 每日任务生成 + 持久化 | ✅ | `daily_tasks` 表，首次登录自动生成 |
| 跳过/换一个/调整难度/加量 | ✅ | `POST /tasks/{id}/skip|replace|adjust` |
| 资料推荐（三因子评分） | ✅ | 短板 40% + 难度 35% + 兴趣 25%，6 条推荐 |
| 7 天不重复 + 不感兴趣反馈 | ✅ | `material_recommendations` 表 |

### 模块 4：AI 发音评测与纠错 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| wav2vec2 + GOP 五维评分 | ✅ | `PronunciationService`（音素/重音/连读/语调/节奏） |
| 模式加权（单词 vs 句子） | ✅ | 单词: 音素 50%/重音 25%/节奏 25%；句子: 各 20% |
| 评测结果持久化 | ✅ | `pronunciation_records` 表 |
| 跟读内容库 API | ✅ | `GET /pronunciation/content`，按类型/等级筛选 |
| 评测历史 API | ✅ | `GET /pronunciation/records`，最近 20 条 |
| IPA 音标展示 | ✅ | 前端 `phonetic_ipa` 字段 |
| 标准音对比播放 | ✅ | Edge TTS 生成标准音 + 并排播放器 |
| 详细评分弹窗（5 Tab） | ✅ | 逐音素/重音能量/F0 曲线/连读词对/节奏时长 |

### 模块 5：流利度与完整性评估 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 五维流利度计算 | ✅ | `FluencyService`（语速/停顿/重复/语法/相关性） |
| 嵌入对话每轮静默评分 | ✅ | `conversation.py` 中调用 |
| 对话结束汇总报告 | ✅ | `/end` 端点返回流利度数据 |

### 模块 6：智能语音对话练习 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| ASR→LLM→TTS 完整管线 | ✅ | WhisperX + qwen-plus + Edge TTS |
| SSE 流式响应 | ✅ | `POST /conversation/stream/speak` |
| 10 轮上下文记忆 | ✅ | `MAX_CONVERSATION_ROUNDS = 10` |
| 4 个 MVP 场景 | ✅ | 自我介绍/问路/购物/餐厅 |
| 对话会话/消息持久化 | ✅ | `conversation_sessions` + `conversation_messages` 表 |
| 对话结束四维评分 | ✅ | 发音 30% + 语法 30% + 词汇 20% + 参与度 20% |
| 难度自适应 | ✅ | A1-A2 基础 / B1 中阶 / B2+ 高阶 Prompt |
| 对话历史 API | ✅ | `GET /conversation/sessions` |

### 模块 7：AI 语法纠错与润色 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 6 类语法错误检测 | ✅ | 时态/主谓一致/冠词/介词/词序/单复数 |
| 错误高亮 + 修正版 + 语法说明 | ✅ | `GrammarView.vue` 差异高亮 + 错误卡片 |
| 润色建议 | ✅ | 礼貌升级/口语化/俚语/缩略/精简 |
| 对话内实时纠错 | ✅ | `asyncio.create_task` 并行，SSE 新增 grammar 事件 |
| 语音输入纠错 | ✅ | `POST /grammar/correct/voice` |

### 模块 8：情景角色扮演 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 3 个内置角色 | ✅ | 面试者/服务员/导游 |
| 角色 Prompt 注入 | ✅ | `LLMService.chat_roleplay_stream` |
| 四维角色评分 | ✅ | 贴合度 40% + 礼仪 25% + 术语 20% + 应对 15% |
| 对话结果持久化 | ✅ | 复用 `conversation_sessions` 表，scene/role_id 字段 |
| 角色说明卡 | ✅ | 前端展示角色目标/常见用语/建议话术 |

### 模块 9：学习资料智能推荐 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 三因子评分算法 | ✅ | 短板 40% + 难度 35% + 兴趣 25% |
| 6 条推荐（视频×2+文章×2+音频×2） | ✅ | `RecommendationService` |
| 7 天不重复 | ✅ | `material_recommendations` 表记录推荐历史 |
| "不感兴趣"反馈 | ✅ | `POST /recommendations/{id}/dislike` |
| 前端推荐页 | ✅ | `RecommendationView.vue` 对接真实 API |

### 模块 10：游戏化闯关学习 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 5 关闯关（A1→B2） | ✅ | `GamificationService` |
| 配音挑战 + 三维评估 | ✅ | 发音 50% + 语调 30% + 情感 20% |
| 积分系统 | ✅ | `user_scores` 表，多种得分规则 |
| 7 种勋章 | ✅ | `user_badges` 表 |
| 每日签到 | ✅ | `POST /gamification/checkin` |
| 排行榜 | ✅ | `GET /gamification/leaderboard` |
| 前端对接 | ✅ | `ChallengeView.vue` 对接真实 API |

### 模块 11：学习社区与社交互动 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 语音挑战广场 | ✅ | `challenge_topics` + `challenge_records` 表 |
| 话题讨论区 | ✅ | `discussion_topics` + `discussion_comments` 表 |
| 学习小组 | ✅ | `groups` + `group_members` 表 |
| 排名/点赞/评论 | ✅ | `CommunityService` |
| 前端社区页 | ✅ | `CommunityView.vue` 对接真实 API |

### 模块 12：学习进度可视化追踪 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 雷达图（五维能力） | ✅ | ECharts RadarChart |
| 趋势折线图 | ✅ | ECharts LineChart |
| 日历热力图 | ✅ | ECharts HeatmapChart |
| 6 项核心统计 | ✅ | `ProgressService` |
| 时间范围切换 | ✅ | 日/周/月/全部 |
| 前端对接 | ✅ | `ProgressView.vue` 对接真实 API |

### 模块 13：学习效果预测与预警 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 线性回归预测 | ✅ | `PredictionService`，最近 30 天综合分 |
| 3 条预警规则 | ✅ | 连续 3 天未学/时长降>50%/发音 7 天未提升 |
| 预警消息推送 | ✅ | `notices` 表 + 通知铃铛 |
| 前端预测页 | ✅ | 集成在 `ProgressView.vue` |

### 模块 14：教师端教学管理后台 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 班级 CRUD + 邀请码 | ✅ | `classes` + `class_students` 表 |
| 作业布置 + 提交查看 | ✅ | `assignments` + `assignment_submissions` 表 |
| 教师点评（反馈+评分） | ✅ | `POST /admin/submissions/{id}/review` |
| 学生报告（雷达图+活动） | ✅ | `GET /admin/students` + `/students/{id}` |
| 前端对接 | ✅ | ClassManageView / HomeworkView / StudentReportView |

### 模块 15：运营管理后台 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| 用户管理（分页+搜索+筛选） | ✅ | `GET /admin/users`，启用/禁用 |
| 数据仪表盘（8 指标） | ✅ | DAU/MAU/留存/总用户/活跃/趋势/类型分布/等级分布 |
| 内容管理（4 类 Tab） | ✅ | `GET /admin/content/{type}`，按需加载 |
| 反馈管理 | ✅ | `user_feedbacks` 表，回复/标记解决 |
| 操作日志 | ✅ | `admin_logs` 表，关键操作自动记录 |
| 前端对接 | ✅ | DashboardView / UserManageView / ContentManageView / FeedbackView |

### 模块 16：智能客服与帮助系统 ✅

| 项 | 状态 | 说明 |
|----|------|------|
| LLM 智能问答 | ✅ | `HelpService`，qwen-plus 驱动 |
| 问题自动分类（5 类） | ✅ | 产品使用/学习建议/技术故障/退款/闲聊 |
| 连续 3 次转人工 | ✅ | 重复检测 + 固定话术 |
| 超范围拒绝 | ✅ | 非学习相关问题固定话术拒绝 |
| LLM 故障降级 FAQ | ✅ | 降级到 `faq_entries` 纯展示 |
| 语音输入 | ✅ | `POST /help/chat/voice`，WhisperX 转写 |
| 前端对接 | ✅ | `HelpView.vue`，打字动画 + 分类标签 |

---

## 三、数据库表清单（32 张）

| # | 表名 | 所属模块 | 模型文件 |
|---|------|----------|----------|
| 1 | `user_profiles` | 用户服务 | `models/user.py` |
| 2 | `assessment_questions` | 测评 | `models/assessment.py` |
| 3 | `assessment_records` | 测评 | `models/assessment.py` |
| 4 | `kg_nodes` | 学习路径 | `models/knowledge_graph.py` |
| 5 | `kg_edges` | 学习路径 | `models/knowledge_graph.py` |
| 6 | `daily_tasks` | 学习路径 | `models/learning.py` |
| 7 | `learning_materials` | 资料推荐 | `models/learning.py` |
| 8 | `material_recommendations` | 资料推荐 | `models/learning.py` |
| 9 | `pronunciation_content` | 发音评测 | `models/pronunciation.py` |
| 10 | `pronunciation_records` | 发音评测 | `models/pronunciation.py` |
| 11 | `conversation_sessions` | 对话/角色扮演 | `models/conversation.py` |
| 12 | `conversation_messages` | 对话/角色扮演 | `models/conversation.py` |
| 13 | `user_skill_scores` | 用户画像 | `models/profile.py` |
| 14 | `user_scores` | 游戏化 | `models/gamification.py` |
| 15 | `user_badges` | 游戏化 | `models/gamification.py` |
| 16 | `dubbing_content` | 游戏化 | `models/gamification.py` |
| 17 | `dubbing_records` | 游戏化 | `models/gamification.py` |
| 18 | `learning_predictions` | 预测 | `models/prediction.py` |
| 19 | `notices` | 预测 | `models/prediction.py` |
| 20 | `challenge_topics` | 社区 | `models/community.py` |
| 21 | `challenge_records` | 社区 | `models/community.py` |
| 22 | `discussion_topics` | 社区 | `models/community.py` |
| 23 | `discussion_comments` | 社区 | `models/community.py` |
| 24 | `groups` | 社区 | `models/community.py` |
| 25 | `group_members` | 社区 | `models/community.py` |
| 26 | `classes` | 教师管理 | `models/admin.py` |
| 27 | `class_students` | 教师管理 | `models/admin.py` |
| 28 | `assignments` | 教师管理 | `models/admin.py` |
| 29 | `assignment_submissions` | 教师管理 | `models/admin.py` |
| 30 | `admin_logs` | 运营管理 | `models/admin.py` |
| 31 | `user_feedbacks` | 运营管理 | `models/admin.py` |
| 32 | `faq_entries` / `support_sessions` / `security_logs` | 智能客服 | `models/support.py` |

> 注：init.sql 含 32 张表（含 `system_config`），ORM 模型覆盖全部业务表。

---

## 四、API 路由清单（14 个路由模块）

| 路由文件 | 前缀 | 端点数 | 说明 |
|----------|------|--------|------|
| `api/auth.py` | `/api/auth` | 6 | 注册/登录/刷新/个人资料 |
| `api/assessment.py` | `/api/assessment` | 5 | 开始/答题/完成/恢复/状态 |
| `api/pronunciation.py` | `/api/pronunciation` | 4 | 评分/参考音/内容库/历史 |
| `api/conversation.py` | `/api/conversation` | 6 | 开始/说话(SSE)/结束/历史 |
| `api/roleplay.py` | `/api/roleplay` | 5 | 开始/说话(SSE)/结束/场景列表 |
| `api/grammar.py` | `/api/grammar` | 2 | 文本纠错/语音纠错 |
| `api/learning_path.py` | `/api/learning-path` | 6 | 任务/跳过/替换/调整/历史 |
| `api/recommendation.py` | `/api/recommendations` | 4 | 推荐列表/不感兴趣/刷新/点击 |
| `api/gamification.py` | `/api/gamification` | 7 | 闯关/配音/积分/勋章/签到/排行榜 |
| `api/progress.py` | `/api/progress` | 4 | 雷达图/趋势/热力图/统计 |
| `api/prediction.py` | `/api/prediction` | 3 | 预测/预警/通知 |
| `api/community.py` | `/api/community` | 9 | 挑战/讨论/小组 CRUD |
| `api/admin.py` | `/api/admin` | 17 | 班级/作业/用户/仪表盘/内容/反馈/学生报告 |
| `api/help.py` | `/api/help` | 2 | 文字客服/语音客服 |

---

## 五、待优化项（非阻塞）

以下为可选优化，不影响功能完整性：

- [ ] Alembic 迁移文件与 init.sql 同步校验
- [ ] 前端全局 loading / error 状态统一处理
- [ ] WebSocket 端点（需求说明书提到 `/ws`，当前用 SSE 替代）
- [ ] 文件上传目录 `uploads/` 管理 + 过期清理
- [ ] AI/ML 推理结果缓存（减少重复 LLM 调用）
- [ ] 浏览器兼容性测试（Chrome 90+ / Edge 90+ / Firefox 88+）
- [ ] 30 天以上数据聚合缓存（仪表盘性能优化）
- [ ] 邀请码 24h 过期刷新机制
- [ ] 完成率自动计算（作业完成率定时任务）
