<script setup>
const competencies = [
  {
    title: '实时语音对话',
    subtitle: '像真人一样自然交流',
    icon: 'Headset',
    color: '#6366F1',
    gradient: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
    highlights: [
      'ASR → LLM → TTS 端到端管线',
      '60+ 真实场景（餐厅/面试/旅行…）',
      '自适应语速与难度，流式秒回',
    ],
  },
  {
    title: '专业发音评测',
    subtitle: '比老师更懂你的发音',
    icon: 'Microphone',
    color: '#10B981',
    gradient: 'linear-gradient(135deg, #10B981, #34D399)',
    highlights: [
      '音素/重音/连读/语调/节奏 五维评分',
      'wav2vec2 + GOP + CTC 强制对齐',
      '音素级波形对比，定位每个发音问题',
      '针对性纠音建议与练习自动生成',
    ],
  },
  {
    title: '个性化学习路径',
    subtitle: 'AI 为你量身定制',
    icon: 'Guide',
    color: '#F59E0B',
    gradient: 'linear-gradient(135deg, #F59E0B, #FBBF24)',
    highlights: [
      '智能测评 → 路径规划 → 内容推荐 → 效果预测',
      '知识图谱（NetworkX BFS/拓扑排序）',
      '四因子推荐算法，精准匹配学习内容',
      '学习趋势预测与流失预警',
    ],
  },
  {
    title: '全场景多年龄段',
    subtitle: '从儿童到职场，人人适用',
    icon: 'UserFilled',
    color: '#3B82F6',
    gradient: 'linear-gradient(135deg, #3B82F6, #60A5FA)',
    highlights: [
      '覆盖儿童 / 青少年 / 大学生 / 职场 / 中老年',
      '日常交流 / 考试备战 / 商务谈判 / 出国留学',
      '游戏化闯关 + 积分勋章，激发学习动力',
    ],
  },
  {
    title: '教学管理一体化',
    subtitle: '不止是学习工具',
    icon: 'School',
    color: '#EC4899',
    gradient: 'linear-gradient(135deg, #EC4899, #F472B6)',
    highlights: [
      '教师端：班级管理 / 作业布置 / 学生报告',
      '运营端：数据看板 / 用户管理 / 内容审核',
      'C 端 + B 端完整闭环',
    ],
  },
  {
    title: '低成本高性能',
    subtitle: '先进技术，可控成本',
    icon: 'CPU',
    color: '#06B6D4',
    gradient: 'linear-gradient(135deg, #06B6D4, #22D3EE)',
    highlights: [
      '国产千问大模型，成本远低于 GPT',
      'ASR / 发音评测本地推理，零 API 费用',
      'TTS 微软免费方案，4 种自然音色',
    ],
  },
]

const userTypes = [
  { icon: 'User', label: '学习者', desc: '提升口语能力，备战考试，职场进阶' },
  { icon: 'Avatar', label: '教师', desc: '管理班级，布置作业，追踪学生进步' },
  { icon: 'OfficeBuilding', label: '学校机构', desc: '部署私有化方案，统一教学管理' },
]
</script>

<template>
  <div class="intro-page">
    <!-- Hero -->
    <section class="hero">
      <h1 class="hero-title">为什么选择 <span class="gradient-text">Lingolab</span></h1>
    </section>

    <!-- 六大核心竞争力 -->
    <section class="competencies-section">
      <h2 class="section-title">核心能力</h2>
      <div class="competency-grid">
        <div
          v-for="c in competencies" :key="c.title"
          class="competency-card"
        >
          <div class="comp-icon" :style="{ background: c.gradient }">
            <el-icon :size="26"><component :is="c.icon" /></el-icon>
          </div>
          <h3 class="comp-title">{{ c.title }}</h3>
          <p class="comp-subtitle">{{ c.subtitle }}</p>
          <ul class="comp-highlights">
            <li v-for="h in c.highlights" :key="h">{{ h }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 学习流程 -->
    <section class="flow-section">
      <h2 class="section-title">三步开始学习</h2>
      <div class="flow-cards">
        <div class="flow-card">
          <div class="flow-icon-wrap" style="background: rgba(99, 102, 241, 0.1); color: #6366F1;">
            <el-icon :size="32"><Microphone /></el-icon>
          </div>
          <h3>开口说</h3>
          <p>选择场景，按下录音，<br>AI 实时转写 + 实时对话</p>
        </div>
        <div class="flow-card">
          <div class="flow-icon-wrap" style="background: rgba(16, 185, 129, 0.1); color: #10B981;">
            <el-icon :size="32"><DataAnalysis /></el-icon>
          </div>
          <h3>AI 分析</h3>
          <p>音素级评测 + 语法纠错 +<br>流利度评估，多维诊断</p>
        </div>
        <div class="flow-card">
          <div class="flow-icon-wrap" style="background: rgba(245, 158, 11, 0.1); color: #F59E0B;">
            <el-icon :size="32"><TrendCharts /></el-icon>
          </div>
          <h3>获得反馈</h3>
          <p>纠音建议 + 地道表达 +<br>学习报告，反馈反哺学习</p>
        </div>
      </div>
    </section>

    <!-- 适用人群 -->
    <section class="users-section">
      <h2 class="section-title">为谁而生</h2>
      <div class="user-cards">
        <div v-for="u in userTypes" :key="u.label" class="user-card">
          <el-icon :size="36"><component :is="u.icon" /></el-icon>
          <h3>{{ u.label }}</h3>
          <p>{{ u.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 底部slogan -->
    <div class="footer-slogan">
      <p class="slogan-main">端到端语音交互 · 五维发音评测 · 个性化学习路径</p>
      <p class="slogan-sub">从测评到进步，全链路 AI 陪伴你的英语口语之旅</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.intro-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl) var(--spacing-huge);
}

/* ========== Hero ========== */
.hero {
  text-align: center;
  padding: var(--spacing-huge) 0 var(--spacing-xxl);
}
.hero-badge {
  display: inline-block;
  padding: 6px 20px;
  background: rgba(var(--color-primary-rgb), 0.08);
  color: var(--color-primary);
  border-radius: 20px;
  font-size: var(--font-size-sm);
  font-weight: 600;
  font-family: var(--font-heading);
  letter-spacing: 0.5px;
  margin-bottom: var(--spacing-xl);
}
.hero-title {
  font-family: var(--font-heading);
  font-size: 56px;
  font-weight: 900;
  line-height: 1.15;
  margin-bottom: var(--spacing-lg);
  letter-spacing: -1.5px;
}
.gradient-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, #A78BFA 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ========== 节标题 ========== */
.section-title {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 800;
  text-align: center;
  margin-bottom: var(--spacing-sm);
}
.section-desc {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
  font-weight: 500;
  margin-bottom: var(--spacing-xxl);
}

/* ========== 六大竞争力 ========== */
.competencies-section {
  margin-bottom: var(--spacing-huge);
}
.competency-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}
.competency-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xxl) var(--spacing-xl);
  transition: all 0.3s ease;
  cursor: default;
  display: flex;
  flex-direction: column;
  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    transform: translateY(-4px);
  }
}
.comp-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: var(--spacing-lg);
}
.comp-title {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 4px;
}
.comp-subtitle {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md);
}
.comp-highlights {
  list-style: none;
  padding: 0;
  margin: 0;
  li {
    font-size: var(--font-size-base);
    font-weight: 500;
    color: var(--color-text-secondary);
    line-height: 2.2;
    padding-left: var(--spacing-md);
    position: relative;
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 10px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--color-primary);
      opacity: 0.5;
    }
  }
}

/* ========== 学习流程 ========== */
.flow-section {
  margin-bottom: var(--spacing-huge);
}
.flow-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}
.flow-card {
  text-align: center;
  padding: var(--spacing-xxl) var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
  cursor: default;
  display: flex;
  flex-direction: column;
  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    transform: translateY(-4px);
  }
}
.flow-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-md);
}
.flow-card h3 {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 var(--spacing-sm);
}
.flow-card p {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
}

/* ========== 适用人群 ========== */
.users-section {
  margin-bottom: var(--spacing-huge);
}
.user-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}
.user-card {
  text-align: center;
  padding: var(--spacing-xxl) var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
  cursor: default;
  display: flex;
  flex-direction: column;
  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    transform: translateY(-4px);
  }
  .el-icon {
    color: var(--color-primary);
    margin-bottom: var(--spacing-md);
  }
  h3 {
    font-family: var(--font-heading);
    font-size: 20px;
    font-weight: 800;
    margin: 0 0 var(--spacing-sm);
  }
  p {
    font-size: var(--font-size-base);
    font-weight: 500;
    color: var(--color-text-secondary);
    line-height: 1.7;
    margin: 0;
  }
}

/* ========== 底部slogan ========== */
.footer-slogan {
  text-align: center;
  padding: var(--spacing-huge) 0 var(--spacing-xxl);
}
.slogan-main {
  font-family: var(--font-heading);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-md);
}
.slogan-sub {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .hero-title { font-size: 36px; }
  .competency-grid { grid-template-columns: 1fr; }
  .flow-cards { grid-template-columns: 1fr; }
  .user-cards { grid-template-columns: 1fr; }
}
</style>