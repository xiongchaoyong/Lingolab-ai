# 操作日志

> 记录每次 PR / AI 辅助操作的摘要

---

## 2026-07-01: 修复听力任务"开始听力"功能缺失

### 变更内容
1. **后端 — 新增资料详情 API**：`GET /api/recommendations/material/{material_id}` 支持 kg_node ID 和 learning_materials 数字 ID 两种查询方式
2. **后端 — TaskItem 新增 `material_id` 字段**：每日任务 API 返回中增加关联资料节点 ID，供听力页面获取资料详情
3. **后端 — RecentStats 新增听力统计**：`listening_count` + `avg_listening_score` 字段
4. **前端 — 新建听力练习页面**：`ListeningView.vue` 三阶段流程（准备→听力中→完成），含 HTML5 音频播放器 + 计时器
5. **前端 — 添加 `/listening` 路由**
6. **前端 — API 层补充**：`completeTaskApi` + `getMaterialDetailApi`
7. **前端 — Store 新增 `completeTask` action**：完成任务后自动更新本地进度
8. **前端 — LearningPathView 修复**：`startTask()` 添加 `listening` 分支，导航到 `/listening?taskId=X`

### 数据库操作
- 删除旧库 → 从 `database-export/full-dump-data+structure.sql` 重建 43 张表（含完整数据）

---

## 2026-07-01: 修复资料推荐"换一批"按钮 429 报错

### 变更内容
1. **后端 — 刷新上限提升**：`get_today_refresh_count` 从 3 次提高到 10 次
2. **前端 — 新增 429 状态码处理**：axios 拦截器增加 429 case，显示 `data?.detail` 友好提示
3. **前端 — 默认错误提示优化**：`default` 分支优先显示 `data?.detail`（后端标准错误字段）
4. **数据库 — 清理旧推荐记录**：重置用户刷新计数器

---

## 2026-07-01: 修复资料推荐"查看"按钮无响应 + 补充国内资料链接

### 变更内容
1. **前端 — RecommendationView 修复**：`handleView()` 点击"查看"按钮 → 调用 click API 记录行为 → 跳转到资料详情页
2. **前端 — 新建资料详情页**：`MaterialDetailView.vue` 展示资料标题/描述/类型/难度/标签/维度/时长，含"打开原文链接"按钮
3. **前端 — 新增 `/material/:id` 路由**
4. **数据库 — kg_nodes 30 条资料 URL 更新**：从 `example.com` 占位符替换为国内网站（哔哩哔哩/知乎/简书/喜马拉雅）
5. **数据库 — learning_materials 扩充**：从 12 条扩展到 30 条（视频/文章/音频各 10 条），URL 同步更新

---

## 2026-06-29: 修复对话音频存储时序 + 文档清理

### 变更内容
1. **修复音频存储时序**：`conversation_stream_speak` 中将 `session["user_audios"].append()` 从 finally 块提前到语法纠错之前，避免流式延迟导致音频文件丢失
2. **清理 introduction.md**：删除末尾残留的草稿内容和核心竞争力板块（内容已迁移至 README.md）
3. **.gitignore 更新**：添加 `backend/uploads/` 和 `frontend/.vite/` 运行时目录

---

### 变更内容
1. **对话场景扩展**：MySQL `conversation_sessions` 表新增 4 个场景枚举值（hotel/airport/hospital/school），前后端同步更新场景映射
2. **游戏化闯关卡片水平布局**：每日闯关/配音挑战/勋章墙从竖直排列改为 CSS Grid 4 列布局，修复 el-row/el-col 缓存问题
3. **配音挑战+勋章墙数据加载修复**：`tab-change` 事件从 `el-tab-pane` 移至 `el-tabs`，切 tab 时触发数据请求
4. **对话+角色扮演场景卡片**：VoiceCallView 和 RolePlayView 场景卡片改为 4×2 CSS Grid 布局
5. **社区语音挑战评分修复**：`asyncio.run()` 在 FastAPI 事件循环中报错，改为同步 `pron_service.score()` 调用，修复分数映射（overall/dimensions 结构）
6. **社区挑战提交音频转码**：上传音频增加 ffmpeg 转 16kHz WAV 步骤，与游戏化接口保持一致
7. **排行榜模拟数据**：创建 `seed_leaderboard_teacher.py`，为 7 个用户生成 208 条积分记录 + 28 条挑战提交记录
8. **教师端模拟数据**：为 xxxcy 用户创建 3 个班级 + 学生 + 作业 + 提交记录
9. **教师端三页面高度修复**：ClassManageView/HomeworkView/StudentReportView 添加固定高度 + flex 布局 + `:close-on-click-modal="false"` 防止弹窗 bug
10. **学生端页面高度修复**：MyClassesView/MyHomeworkView 同样固定高度 + 弹窗修复
11. **学生详情后端报错修复**：`admin.py` 中 `s.source_type` → `s.source`（UserSkillScore 模型字段名修正）
12. **README.md 全面更新**：技术栈更新（千问/WhisperX/wav2vec2/Edge TTS）、16 模块全部标记已实现、新增 6 大核心竞争力、项目结构同步实际布局

## 2026-06-26: 后台管理服务模块完善

### 变更内容
1. **教师端前端接入**：修改路由守卫 + TopNavLayout，admin 角色可访问教师端 3 个页面（班级管理/作业管理/学生报告），教师端页面已存在只需导航接入
2. **内容管理 CRUD**：后端新增 POST/PUT/DELETE 接口 + AdminService 方法 + Pydantic Schema，前端 ContentManageView 增加新增/编辑/删除功能
3. **仪表盘留存率**：实现 D1/D7 留存率计算（基于 UserSkillScore 活跃用户交叉统计），前端新增 2 个指标卡片
4. **修复配音内容字段映射**：dubbing 查询中 dialogue_text → subtitle, difficulty_level → difficulty
5. **修复内容管理字段映射**：`get_content_list` 中 questions 引用不存在的 `question_type` → 改为 `dimension`
6. **学生端班级+作业**：新增 `StudentService` + `/api/student/*` 接口 + 前端 `MyClassesView` / `MyHomeworkView` + 导航栏「班级作业」入口
7. **模块六全面审计修复**：
   - 班级名称/描述字段长度校验（50/200字符）
   - 邀请码24h过期 + 过期刷新接口 + 前端刷新按钮
   - 加入班级时检查邀请码过期 + "邀请码已过期"错误提示
   - 作业提交截止时间检查 + "作业已截止"错误提示
   - 管理员不能禁用自己（后端校验）
   - 禁用用户需二次确认弹窗
   - 仪表盘补全10项指标（总时长/人均时长/对话完成率/日新增）
   - 作业提交列表增加录音播放按钮
	25. **全模块模拟数据种子**：创建 `backend/seed_all_modules.py` 为 xxxcy 用户(ID=4)生成10类模拟数据：发音练习27条、对话会话6个(37条消息)、配音记录4条、语音挑战3条、学习资料9条、社区互动、每日任务31条、积分/徽章/预测、通知12条、技能分数补充
	26. **客服UI增强**：HelpView 语音输入优化 + 消息展示改进 + 转人工流程优化
	27. **Logo 放大**：TopNavLayout 左上角 Lingolab 字体从 16px 放大到 24px
	28. **个人情况说明**：ProfileSummaryView 集成用户画像数据展示

## 2026-05-25

| 时间 | 操作 | 描述 | 成员 | AI 生成部分已通读 |
|------|------|------|:---:|:---:|
| 09:16 | 项目初始化 | 创建 CLAUDE.md、README.md，配置远程仓库并推送至 main 分支 | XCY | ✅ |
| 09:20 | 补充文档 | 新增 ai-log.md，更新经验教训 | XCY | ✅ |
| 09:22 | 补充文档 | ai-log.md 新增成员列，明确操作归属 | XCY | ✅ |
| 09:24 | 修正流程 | 补充遗漏的操作记录 | XCY | ✅ |
| 09:25 | 修正流程 | 确立「先更新 log 再推送」规则 | XCY | ✅ |
| 09:27 | 修正流程 | 规范分支策略：每次开发前自动拉取最新 dev 并创建 feat 分支 | XCY | ✅ |
| 09:34 | 共享配置 | 创建 .claude/settings.json 团队共享配置，新增 .gitignore | XCY | ✅ |
| 09:37 | 修正流程 | 修正 ai-log.md 时间戳为实际提交时间 | XCY | ✅ |
| 09:41 | 技能配置 | 注册两个自定义 Skill：requirements-clarity（需求澄清）和 lyra（提示词优化） | XCY | ✅ |
| 09:43 | 补充文档 | CLAUDE.md 新增「自定义技能」章节，记录两个 Skill 说明 | XCY | ✅ |
| 09:45 | 技能配置 | 将 Skill 文件移至 .claude/skills/ 目录，更新配置路径 | XCY | ✅ |
| 10:09 | 技能重命名 | requirements-clarity → product-manager，lyra → prompt-polish，改用目录+SKILL.md自动发现 | XCY | ✅ |
| 10:10 | 项目里程碑 | 项目初始化完成，dev 合并至 main 分支 | XCY | ✅ |
| 15:00 | 测试推送 | 在 README.md 添加项目标语 "Speak smarter, not harder."，测试 git push 流程 | DJQ | ✅ |

## 2026-05-27

| 时间 | 操作 | 描述 | 成员 | AI 生成部分已通读 |
|------|------|:-----|:---:|:---:|
| 17:30 | 技能配置 | 新增 drawio-skill（AI 绘图），更新 CLAUDE.md 技能表；README 项目名改为 Lingolab-ai | XCY | ✅ |
| 17:35 | 技能配置 | 新增 ui-ux-pro-max 技能（UI/UX 设计智能，67 风格/161 配色/57 字体），通过 uipro-cli 安装 | XCY | ✅ |
| 17:48 | 流程规范 | Git 工作流新增拉取 main 步骤，确保每次开发前同步上游最新代码 | XCY | ✅ |
| 21:13 | 需求分析 | 完成 PRD 整体分析（用户角色/系统边界/模块依赖/优先级）+ 模块1-3 详细需求（画像/测评/学习路径），绘制系统边界+模块依赖两张架构图，测试 ui-ux-pro-max 技能生成首页 | XCY | ✅ |

## 2026-05-28

| 时间 | 操作 | 描述 | 成员 | AI 生成部分已通读 |
|------|------|------|:---:|:---:|
| 08:54 | 需求分析 | 完成全部 16 模块 PRD（P0/P1/P2/P3），含详细流程/边界/验收标准；PRD 汇总总结；创建全流程项目计划文档 project-plan.md | XCY | ✅ |
| 15:30 | 补充文档 | 新增 Claude Code 团队使用指南（claude-code-团队使用指南.md）和项目文件目录说明（project-directory-guide.md）；更新 .gitignore 忽略 drawio 备份文件 | XCY | ✅ |
| 15:35 | 推送 | push 至 origin/dev（2 commits：团队使用指南 + 项目目录说明 + .gitignore 修正） | XCY | ✅ |
| 21:00 | 架构设计 | 绘制项目环境架构图（展现层/应用层/能力层/数据层/基础设施层）+ 系统功能结构图（用户端/管理端/客服子系统），完成技术栈分析与能力层技术标注 | XCY | ✅ |

## 2026-05-29

| 时间 | 操作 | 描述 | 成员 | AI 生成部分已通读 |
|------|------|------|:---:|:---:|
| 09:00 | 需求分析 | 完成 PRD v1.0 定稿（16 模块完整需求），新建 docs/lingolab-ai-v1.0-prd.md | XCY | ✅ |
| 09:10 | 流程规范 | 新建功能模块分析文档工作流（三阶段：子功能拆解→用例图→详细规格+流程图），定义输出模板和目录规范 | XCY | ✅ |
| 09:15 | 技能配置 | 新增 module-analysis 技能（功能模块分析），更新 CLAUDE.md 技能表 | XCY | ✅ |
| 09:20 | 文档清理 | 删除 docs/project-plan.md（已被 PRD 和工作流文档取代） | XCY | ✅ |
| 09:50 | 技能重构 | 重命名 product-manager → requirements-clarity，新增需求分析师智能体（deepseek-v4-pro，自动触发），清理根目录重复文件，更新 CLAUDE.md 引用 | XCY | ✅ |

## 2026-05-30

| 时间 | 操作 | 描述 | 成员 | AI 生成部分已通读 |
|------|------|------|:---:|:---:|
| 11:00 | 工作流优化 | 精炼 module-analysis 详细规格说明模板，保留「介绍/输入/处理/输出」四段式结构，每子功能 ≤30 行，去除时序/错误码/接口URL冗余内容 | XCY | ✅ |

## 2026-05-31

| 时间 | 操作 | 描述 | 成员 |  |
|------|------|------|:---:|:---:|
| 12:00 | 模块分析 | 完成全部16模块用例图+流程图+详细规格Word文档：绘制模块9-16用例图(8个)+流程图(6个)，批量导出PNG(17张)，修正gen_doc.py图片路径，重新生成模块4-16全部Word文档(含嵌入图片) | XCY | ✅ |
| 17:50 | 模块分析 | 使用drawio-skill手写XML生成模块一7张图(UML用例图+6张流程图)，直线无箭头关联线，正交路由+waypoint分支，黑白PingFang SC紧凑布局，导出PNG@2x插入主文档 | XCY | ✅ |
| 16:23 | 模块分析 | 重新生成模块1-用户服务全套图文档：用例图1个 + 流程图5个(1.1注册/1.2登录JWT/1.5自适应测评/1.6口语评测/1.8学习路径)，手动编写drawio XML精确控制线段对齐，导出PNG后嵌入Word文档(含9个子功能详细规格)，输出路径 docs/功能模块需求分析/模块1-用户服务/ | XCY | ✅ |
| 19:00 | 模块分析 | 合并模块1子功能3.2.4测评三张流程图(自适应分发+口语评分+进度保存)为一张精简联合流程图，更新Word文档图片和标题，删除旧文件 | XCY | ✅ |
| 20:00 | 模块分析 | 完成模块2-学习服务全部8张图(UML用例图+7张子功能流程图)：发音评测五维评分、音素纠错定位、语音对话交互、AI回复生成(CEFR等级策略)、流利度五维评估、语法6类错误检测、角色扮演对话，导出PNG@2x插入主文档 | XCY | ✅ |
| 21:30 | 模块分析 | 完成模块3-7全部15张图：模块3个性化推荐(3张:UML+每日任务+规则推荐)、模块4激励服务(5张:UML+闯关+勋章+统计+预警)、模块5社区服务(3张:UML+语音挑战+学习小组)、模块6后台管理(2张:UML+作业布置)、模块7智能客服(2张:UML+文字问答)，全部占位标记已替换 | XCY | ✅ |



## 2026-06-04

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 10:00 | PRD 迭代 | PRD v1.1 模型架构重构：Whisper→Paraformer→WhisperX、Deepseek→deepseek-v4-flash、Edge TTS→豆包TTS，发音评测从讯飞/驰声→Echoic→wav2vec2(Meta)，管线化架构，延迟目标调整为5s，新增成本分析(全栈月费约15元)；同步更新 CLAUDE.md | XCY  |  ✅   |
| 20:00 | 模型验证 | WhisperX + wav2vec2 + Edge TTS 三模型实测验证：WhisperX small 转录 1.3s + 单词对齐 0.1s (Apple M4 CPU int8)，wav2vec2 GOP 发音评分 MPS 加速通过，Edge TTS 4音色 SSML 句级时间戳通过；TTS 方案回退：豆包 TTS(收费)→Edge TTS(免费) | XCY | ✅ |
| 20:30 | 文档更新 | 更新 CLAUDE.md + model-architecture-v1.1.md + lingolab-ai-v1.0-prd.md，豆包 TTS→Edge TTS，新增实测验证章节(含耗时/设备/模型存储位置/关键发现)，修正环境变量配置 | XCY | ✅ |

## 2026-06-05

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 10:00 | 后端骨架 | 搭建 FastAPI 项目骨架：创建 app/ 目录结构、config.py(Settings)、database.py(SQLAlchemy)、models/__init__.py(Base+TimestampMixin)、.env.example、main.py(含 CORS+lifespan+health)；补全 requirements.txt 依赖 | XCY | ✅ |
| 10:30 | 发音评测 | 实现发音评测模块：PronunciationService(wav2vec2+GOP)封装、score_audio 异步接口(ThreadPoolExecutor)、POST /api/pronunciation/score；Schema 对齐前端 PronunciationView 的 {overall, dimensions, errors} 格式；过滤 CTC 空格 token；服务启动模型预加载验证通过 | XCY | ✅ |
| 10:30 | 规范更新 | CLAUDE.md 新增编码完成规则：每次编码后总结+追加 ai-log.md+再 commit | XCY | ✅ |
| 11:00 | 前后端集成 | 前端发音评测对接真实后端：VoiceRecorder 增加 MediaRecorder 真实录音、新建 api/pronunciation.js、vite 代理 /api→localhost:8000、PronunciationView 替换 Mock 为真实 API | XCY | ✅ |
| 11:30 | bug修复 | 修复录音 mimeType 不支持错误（不指定格式用浏览器默认 webm）、修复 Content-Type boundary 丢失（axios 默认 JSON header 冲突）、后端加 ffmpeg 转码支持任意音频格式 | XCY | ✅ |
| 12:00 | 功能增强 | 发音页面新增「查看详细评分」弹窗：逐音素色块+表格、评分说明（wav2vec2原理/GOP公式/流程图/评级标准/版本限制） | XCY | ✅ |
| 12:30 | 文档整理 | 创建 docs/功能实现.md：系统梳理五维评分含义+技术方案+当前状态+分阶段路线，整理自问答讨论 | XCY | ✅ |
| 13:00 | 功能实现 | 实现重音位置+语调曲线评分：librosa RMS能量包络检测重音变化、librosa PYIN提取F0基频+线性趋势拟合判断语调走向、综合分改为已有维度加权平均、Schema新增analysis_detail分析说明 | XCY | ✅ |
| 13:30 | 可视化 | 重音+语调增加可视化数据：后端返回每音素归一化能量值+重音标记+F0曲线采样点；前端详情弹窗新增「可视化分析」Tab | XCY | ✅ |
| 14:00 | 可视化重构 | 可视化拆为两个独立Tab页「重音位置分析」「语调曲线分析」，每个Tab含分析结论卡片+图表+模型输出数据网格（原始指标+通俗解释） | XCY | ✅ |
| 14:30 | 对比播放 | 新增发音对比功能：后端 POST /api/pronunciation/reference-audio（Edge TTS Jenny 生成标准音MP3流）、前端评分结果页并排显示双播放器（你的录音🎤 VS 标准发音🎧）、并行请求评分+标准音不增加延迟 | XCY | ✅ |
| 15:00 | 播放器重构 | 音频播放器从结果页移至详情弹窗内，自定义样式（圆形播放按钮+波形动画条+时间显示+VS徽章）、隐藏audio元素由自定义UI控制、requestAnimationFrame驱动波形动画、弹窗固定60vh高度可滚动 | XCY | ✅ |
| 15:30 | 连读评分 | 实现连读表现评测：WhisperX small 词级时间戳+G2P 辅元连读条件检测+词间间隙gap评分、Schema新增LinkingPair/LinkingVizData、五维中「连读表现」替换占位维度、前端新增「连读表现」Tab（词对表格+gap色标+模型输出数据网格） | XCY | ✅ |
| 16:00 | 节奏感评分 | 实现节奏感评测：基于CTC对齐音素时长分布、变异系数CV+异常停顿检测(>2x均值)、CV<0.3自然/CV>0.8严重不均、前端新增「节奏感」Tab（时长柱状图+异常停顿标红+模型输出数据网格） | XCY | ✅ |

## 2026-06-22

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 10:00 | 数据库 | 评审需求说明书数据字典(30张表)，修正缺失字段(user_profiles补email+role、system_config补全)、优化数据类型(groups表SMALLINT)、补全索引+ENUM定义，创建 backend/sql/init.sql(31张表)并执行初始化 | XCY | ✅ |
| 10:30 | 发音评测 | 综合分改为PRD要求的模式加权：单词模式(音素50%/重音25%/节奏25%)、句子模式(音素40%/重音15%/连读15%/语调15%/节奏15%)，前后端同步传递mode参数 | XCY | ✅ |
| 11:00 | 导航重构 | 按需求文档7个模块重构导航栏：合并模块2为「学习中心」下拉菜单(发音评测/AI对话/角色扮演)、模块3「学习路径」下拉、模块4「学习进度」下拉、模块5「社区」、模块7「帮助」、模块6「后台管理」按角色显示；hover触发下拉子菜单，点击父级进入第一子项；路由恢复独立页面 | XCY | ✅ |
| 11:30 | 项目规划 | 创建 docs/TODO.md 待办事项文档，按7模块+基础设施梳理约50项任务，标注P0-P3优先级 | XCY | ✅ |
| 14:00 | 对话模块 | 后端切换阿里百炼DashScope、新建ASR服务(WhisperX转录+词级时间戳)+TTS服务(Edge TTS语音合成)、前端对话路由从学习布局改为独立全屏路由、删除旧ConversationView由VoiceCallView替代 | XCY | ✅ |
| 15:00 | 对话评分 | 对话评分综合报告v2丰富版：后端Schema新增utterances/transcript/text_dimension_details/scoring_methodology字段、LLM评分提示升级(每维度feedback+strengths+weaknesses详评)、/end端点保留完整发音评分+对话记录+方法论；前端报告页重构为多节可滚动布局(综合分→语音评测→文本评测→对话记录→改进建议)、新建UtteranceDetailPanel共享组件(逐音素评分表+重音能量图+语调F0曲线+连读词对表+节奏时长图) | XCY | ✅ |
| 16:00 | 角色扮演+UI | 角色扮演模块后端+前端API接入：新增LLM服务(chat_roleplay/chat_roleplay_stream/score_roleplay四维评分：角色贴合度/场景礼仪/专业术语/应对能力)+3个内置场景Prompt(interviewee/waiter/guide)、新建api/roleplay.py+schema；淡紫可爱风UI改版(品牌色#A78BFA、Quicksand+Nunito字体、马卡龙辅助色系)+路由扁平化(Introduction合并进TopNavLayout、/home重定向到/)+CLAUDE.md同步更新 | XCY | ✅ |

## 2026-06-23

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 15:00 | 开发规范 | 基于模块2开发经验提炼AI协作开发规范(ai-collaboration-standards.md)，涵盖项目结构/前端Vue3模式/后端FastAPI模式/前后端协作/开发工作流+AI提示词模板，供小组成员统一遵循 | XCY | ✅ |

## 2026-06-24

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 08:30 | 用户认证 | 实现模块1-3.2.1~3.2.3 用户注册/登录/个人中心：后端新建UserProfile模型+auth Pydantic Schema+JWT安全工具+auth路由(注册/登录/查个人资料/更新个人资料含乐观锁)、前端重写auth store调用真实API+LoginView移除Mock数据+RegisterView增加email字段+新建ProfileView个人资料页、路由注册/profile | XCY | ✅ |
| 09:00 | 水平测评 | 实现模块1-3.2.4 英语水平智能测评：后端新建AssessmentQuestion/AssessmentRecord模型+assessment Schema+assessment路由(POST /start返回10题按维度抽取、POST /submit客观题判分+口语题默认60分+CEFR定级+写入记录+更新user_profiles)、数据库种子数据10道题、前端新建api/assessment.js+重写assessment store对接真实API(snake_case→camelCase映射)+AssessmentView适配异步流程(移除逐题即时判对错) | XCY | ✅ |
| 10:00 | Bug修复 | 口语题卡死修复：VoiceRecorder.vue 中 `mimeType` 未定义导致 ReferenceError，emit('complete') 无法触发，改为 `mediaRecorder.mimeType \|\| 'audio/webm'`；测评完成后禁止重测：路由守卫检查 assessment_completed 状态 | XCY | ✅ |
| 11:00 | 模块3 | 知识图谱驱动的个性化学习路径：Phase 1-6 全部完成。NetworkX+MySQL方案（纯Python，无需Neo4j）。KG模型（kg_nodes/kg_edges/daily_tasks/material_recommendations），129节点+292边种子数据。KnowledgeGraphService（NetworkX内存图+BFS/拓扑排序），RecommendationService（四因子评分：短板40%+难度30%+兴趣20%+新颖度10%+六步任务生成）。API路由（GET /api/learning-path/tasks、POST skip/replace/adjust-difficulty、GET history、GET /api/recommendations/、POST dislike/refresh/click）。前端 API层+Pinia Store+LearningPathView/RecommendationView 接入真实数据 | XCY | ✅ |
| 14:00 | TTS优化 | Edge TTS 后端预取优化：将 TTS 合成从串行改为并行（asyncio.create_task），在 SSE 流结束前提前启动 TTS，消除串行等待延迟；新增 audio_utils.py 共享音频工具（提取 convert_to_wav 消除 conversation/roleplay 重复代码） | XCY | ✅ |
| 15:00 | 语法纠错 | 模块7 AI语法纠错与润色全链路实现：后端新建 schemas/grammar.py（GrammarError/GrammarCorrectResponse）+ api/grammar.py（POST /correct 文本纠错、POST /correct/voice 语音纠错）+ llm.py 新增 correct_grammar 方法（temperature=0.3）；前端新建 GrammarView.vue 独立页面（双模式输入+差异高亮+错误卡片+润色建议）+ 路由注册 + 导航入口；conversation.py + roleplay.py 对话内实时纠错（asyncio.create_task 并行执行 grammar_task，不增加延迟，SSE 新增 grammar 事件）；前端 VoiceCallView + RolePlayView 新增可折叠语法纠错卡片（错误类型颜色标签+中英文解释） | XCY | ✅ |
| 16:00 | 测评P0修复 | 测评模块6项P0修复：①llm.py修复score_fluency/correct_grammar/score_speaking缩进错误（模块级函数→类方法）；②测评API重写为逐题提交+自适应难度（CEFR数值映射A1-C2:1.0-6.0，得分≥60升0.5级/<60降0.5级，钳制[1.0,6.0]）；③新增POST /answer（口语题ASR+LLM四维评分）+ POST /complete（四维均分→CEFR定级+短板分析）；④Schema新增AssessmentAnswerResponse；⑤题库扩充至30题（A2:9/B1:11/B2:10，听力8+口语6+阅读8+语法8）；⑥前端适配：API层新增answerQuestionApi/completeAssessmentApi，Store重构为逐题提交流程（submitAndAdvance+audioBlob），AssessmentView捕获录音blob+评分中加载状态，路由守卫强制未测评用户跳转/assessment | XCY | ✅ |

## 2026-06-25

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 09:00 | 模块4 | 激励服务模块全栈实现：①后端 gamification.py（GamificationService 积分/勋章/签到/排行榜）+ progress.py（PredictionService 线性回归预测达标日期+预警规则检查）+ API路由 + Schema；②前端 ProgressView.vue 重写（雷达图+趋势折线图+日历热力图+统计卡片+预测卡片+预警面板）+ TopNavLayout 通知铃铛动态未读数+60s轮询；③种子数据：71技能分+39积分+5勋章+1预测+5通知 | XCY | ✅ |
| 10:00 | 模块5 | 社区服务模块全栈实现：①后端 models/community.py 7个ORM模型（复用groups/group_members表）+ schemas/community.py 16个Pydantic Schema + services/community.py CommunityService + api/community.py 9个REST端点；②前端 CommunityView.vue 重写（语音挑战广场+排行榜+讨论区+点赞+评论+学习小组+加入/退出），全部接入真实API；③种子数据：3挑战+3帖子+6评论+4小组 | XCY | ✅ |
| 10:30 | 模块6 | 后台管理服务模块全栈实现：①后端 models/admin.py 5个ORM模型（classes/class_students/assignments/assignment_submissions/admin_logs）+ schemas/admin.py Pydantic Schema + services/admin.py（TeacherService班级+作业+点评 / AdminService用户管理+仪表盘）+ api/admin.py 12个REST端点（教师端8个+运营端4个）+ role-based access control；②前端 api/admin.js 11个API函数 + stores/admin.js Pinia Store + 重写4个页面（ClassManageView班级CRUD+邀请码+学生列表、HomeworkView作业布置+提交查看+教师点评、UserManageView分页搜索筛选+启用禁用、DashboardView ECharts指标卡片+趋势图+饼图+类型分布）；③种子数据：教师+管理员账号+3班级+6学生+3作业+10提交 | XCY | ✅ |
| 11:00 | 模块7 | 智能客服与帮助系统全栈实现：①后端 schemas/help.py（ChatRequest/ChatResponse）+ services/help.py（HelpService：LLM问题分类5类别+重复检测3次转人工+固定话术降级）+ api/help.py（POST /chat 文字客服、POST /chat/voice 语音客服→WhisperX转写→LLM回复）；②llm.py 新增 _call_bailian/_raw_chat/_raw_chat_messages 底层方法供客服服务调用；③前端 api/help.js（chatText/chatVoice）+ HelpView.vue 接入真实API（LLM聊天+分类标签+转人工提示+语音输入+打字动画+加载状态） | XCY | ✅ |

## 2026-06-26

| 时间  | 操作     | 描述                                                         | 成员 |      |
| ----- | -------- | :----------------------------------------------------------- | :--: | :--: |
| 10:00 | 测评增强 | 测评模块3项增强：①30天重测评限制（start端点检查last_assessment_at，未满30天返回403+剩余天数）；②全对/全错追加题（10题全对→追加C2口语确认题、全错→追加A1听力基础题，total_questions动态调整）；③会话持久化（POST /restore端点从AssessmentRecord重建内存会话、前端store调restoreSessionApi恢复localStorage+后端双端同步） | XCY | ✅ |
| 11:00 | 发音持久化 | 发音评测模块增强：评测结果写入pronunciation_records表+GET /content跟读内容库API+GET /records评测历史API+前端替换硬编码为后端API加载+历史记录弹窗 | XCY | ✅ |
| 12:00 | 对话持久化 | 对话模块增强：会话/消息持久化到DB+MAX_CONVERSATION_ROUNDS=10+GET /sessions历史API | XCY | ✅ |
| 13:00 | 角色扮演持久化 | 角色扮演模块DB持久化：/start创建会话、/stream/speak保存每轮消息、/end更新四维评分到DB | XCY | ✅ |
| 20:00 | 答辩文档 | 生成答辩梳理文档(docs/答辩梳理-功能模块与技术链路.md)，涵盖系统架构、16模块业务功能/技术实现/数据链路、核心AI技术链路详解、数据库表结构总览、前端架构、项目亮点总结 | XCY | ✅ |
| 21:00 | 管理页面真实API | 3个管理页面对接真实API：①学生报告（GET /admin/students + GET /admin/students/{id}，ECharts雷达图+活动时间线）；②内容管理（GET /admin/content/{type}，4个tab按需加载测评题/跟读/资料/配音）；③反馈管理（新建user_feedbacks表+UserFeedback ORM+GET /feedbacks+POST reply+PUT resolve，前端FeedbackView替换mock数据+状态筛选+分页+回复弹窗）+ seed_feedback.py测试数据 | XCY | ✅ |
| 22:00 | 模块审查+测试 | 逐模块功能审查+流程文档+单元测试：①模块1-16功能实现审查（全部完成度100%）；②模块流程链路文档（模块1-3功能流程+技术架构）；③模块1测试（test_auth.py 41用例）；④模块2测试（test_assessment.py 44用例）；⑤模块3审查+修复（新颖度纳入评分+刷新限3次）+测试（test_learning_path.py 46用例）；分支 feat/module-1~3-test | XCY | ✅ |
| 22:30 | 模块4审查+测试 | 模块4智能语音对话审查+流程文档+测试：①功能审查（全部功能已实现，无缺失）；②流程链路文档补充模块4（开始对话/用户说话管线/TTS播放/结束评分双层体系）；③测试（test_conversation.py 43用例：流利度评级9+单词计数6+重复检测6+算法流利度7+多轮汇总6+Schema15）；分支 feat/module-4-test | XCY | ✅ |
| 23:00 | 模块5审查+修复+测试 | 模块5流利度评估审查+修复+流程文档+测试：①审查发现conversation_messages的fluency_scores/grammar_check列未写入→修复stream/speak端点持久化；②流程链路文档补充模块5（每轮静默评分+结束五维汇总+报告展示）；③测试（test_fluency.py 22用例：语速4+停顿3+重复5+结构5+汇总5）；分支 feat/module-5-test | XCY | ✅ |
| 23:30 | 模块6审查+测试 | 模块6 AI语法纠错审查+流程文档+测试：①功能审查（全部功能已实现：独立纠错API文本+语音、对话/角色扮演asyncio并行纠错+SSE grammar事件+DB持久化、前端双模式输入+差异高亮+错误卡片+润色建议）；②流程链路文档补充模块6（独立文本/语音纠错→对话内实时纠错→角色扮演纠错）；③测试（test_grammar.py 12用例：Schema3+响应4+降级3+类型2）；分支 feat/module-6-test | XCY | ✅ |
| 23:45 | 模块7审查+测试 | 模块7情景角色扮演审查+流程文档+测试：①功能审查（全部功能已实现：3角色场景interviewee/waiter/guide+8个API端点流式+非流式+双层评分角色四维60%+语音五维40%+流利度五维+语法纠错并行+TTS预取+内存+DB双写持久化）；②流程链路文档补充模块7（开始角色扮演→用户说话管线→TTS播放→结束双层评分）；③测试（test_roleplay.py 22用例：Schema8+角色配置5+轮次限制1+评分权重6+降级2）；分支 feat/module-7-test | XCY | ✅ |
| 23:55 | 模块8审查+测试 | 模块8 AI发音评测审查+流程文档+测试：①功能审查（全部功能已实现：POST /score五维评分wav2vec2+GOP+CTC对齐+模式加权单词/句子+POST /reference-audio标准音对比+GET /content跟读内容库+GET /records评测历史+持久化pronunciation_records+画像摄入）；②流程链路文档补充模块8（发音评测五维管线→内容库→历史记录→参考音频对比）；③测试（test_pronunciation.py 19用例：Schema10+评分权重4+音素建议3+内容/记录2）；分支 feat/module-8-test | XCY | ✅ |
| 00:10 | 服务模块4审查+测试 | 服务模块4激励服务剩余子模块（游戏化+进度追踪+预测预警）审查+流程文档+测试：①功能审查（游戏化：9端点每日闯关5关+配音挑战三维评分+积分8规则+勋章7枚+排行榜；进度：4端点五维雷达图+趋势折线图+日历热力图+统计卡片；预测：6端点线性回归预测+3条预警规则+通知系统）；②流程链路文档补充模块10/12/13；③测试（test_service_module4.py 34用例：游戏化18+进度9+预测7）；分支 feat/service-module-4-test | XCY | ✅ |
| 00:20 | 服务模块5审查+测试 | 服务模块5社区服务审查+流程文档+测试：①功能审查（全部功能已实现：语音挑战3端点+话题讨论5端点+学习小组2端点，共9端点+16 Schema）；②流程链路文档补充模块11（语音挑战广场→话题讨论→学习小组）；③测试（test_community.py 19用例：挑战6+帖子4+评论3+点赞2+小组4）；分支 feat/service-module-5-test | XCY | ✅ |
| 00:30 | 服务模块6审查+测试 | 服务模块6管理服务审查+流程文档+测试：①功能审查（资料推荐4端点四因子评分+每日刷新限3次；教师管理8端点班级CRUD+邀请码+作业布置+提交点评+学生列表；运营6端点用户分页搜索+启用禁用+仪表盘8指标+ECharts+内容管理+反馈回复解决）；②流程链路文档补充模块9/14/15；③测试（test_service_module6.py 28用例：推荐5+班级4+学生2+作业6+用户管理3+仪表盘3+反馈5）；分支 feat/service-module-6-test | XCY | ✅ |
| 00:40 | 服务模块7审查+测试 | 服务模块7客服服务审查+流程文档+测试：①功能审查（全部功能已实现：POST /chat文字客服+POST /chat/voice语音客服WhisperX转写，HelpService LLM分类5类+超范围固定话术+连续3次重复转人工+LLM回复+降级FAQ，前端FAQ面板4分类11条+聊天面板+语音输入+打字动画+分类标签）；②流程链路文档补充模块16（文字客服→语音客服→FAQ预设回答）；③测试（test_service_module7.py 19用例：Schema7+FAQ3+重复检测5+常量4）；分支 feat/service-module-7-test | XCY | ✅ |
| 10:00 | 客服+UI增强 | 多项UI和功能增强：①智能客服取消分类限制直接LLM回复+用户气泡右对齐+客服端移除分类标签；②AI对话+角色扮演对话文字加大加粗(18px/600)+(未识别到语音)跳过语法检测；③角色扮演页面全屏背景(FullSCREEN_ROUTES添加/role-play)；④学习路径新增个人情况说明独立页面(/profile-summary)四卡片展示画像+维度分数+统计+推荐算法；⑤用户头像上传功能(后端avatar端点+静态文件服务+前端ProfileView上传预览+TopNavLayout/HomeView头像同步)；⑥修复导航栏下拉菜单bug(个人设置触发登出→handleCommand分派)；⑦Vite添加/static代理 | XCY | ✅ |
