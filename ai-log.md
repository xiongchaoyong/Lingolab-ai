# 操作日志

> 记录每次 PR / AI 辅助操作的摘要

---

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
