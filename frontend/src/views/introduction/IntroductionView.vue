<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const pipeline = [
  { label: '语音输入', tech: 'Whisper ASR', icon: 'Microphone', color: 'var(--color-success)' },
  { label: '文本理解', tech: 'LLM 意图识别', icon: 'ChatDotRound', color: 'var(--color-primary)' },
  { label: '多维评分', tech: 'GOP + GEC', icon: 'DataLine', color: 'var(--color-warning)' },
  { label: '智能回复', tech: 'DeepSeek', icon: 'Service', color: '#8B5CF6' },
  { label: '语音合成', tech: 'TTS 输出', icon: 'Headset', color: 'var(--color-danger)' },
]

const steps = [
  {
    title: '个性化任务推荐', tag: '推荐',
    scene: '首页显示：「今日推荐：国际项目电话会议（匹配你的 B1 水平）」',
    techs: ['BERT 文本特征', '协同过滤', '强化学习路径规划'],
  },
  {
    title: '语音实时转写', tag: 'ASR',
    scene: '小王按下麦克风："the backend... we already finish the API..."——系统流式转写，边说边出字',
    techs: ['Whisper 语音识别', 'VAD 端点检测', '流式推理'],
  },
  {
    title: '多维度口语评分', tag: '评分',
    scene: '弹窗评分—发音78分(database重音错)、语法65分(have→has)、流利度70分(uh填充词过多)',
    techs: ['GOP 发音评分', 'GECToR 语法纠错', 'Sentence-BERT 语义相似度'],
  },
  {
    title: '波形可视化对比', tag: '可视化',
    scene: '用户发音波形 vs 标准发音波形并排对比，重音偏移位置一目了然',
    techs: ['音素级强制对齐', 'librosa 频谱提取', 'Canvas 波形绘制'],
  },
  {
    title: '针对性纠音练习', tag: '练习',
    scene: '系统自动生成纠音卡片—播放标准音→跟读→实时反馈「重音对了！试试放进句子」',
    techs: ['自适应练习生成', '轻量级 GOP 模型', '手机端实时评测'],
  },
  {
    title: 'AI 给出地道表达', tag: 'LLM',
    scene: 'AI 伙伴："You could say we\'ve finished the API, but we\'re still working on the database issue."',
    techs: ['大语言模型生成', '语法润色', '难度自适应'],
  },
  {
    title: '改进后再测一次', tag: '反馈',
    scene: '小王重新说→AI实时显示：语法正确✓ 发音85分✓ "should be resolved 比 will be resolved 更自信"',
    techs: ['实时 ASR', '增量 GEC 检查', '正向激励反馈'],
  },
  {
    title: '生成学习报告', tag: '报告',
    scene: '词汇丰富度：中等 | 语法错误3处→1处(进步中) | 薄弱音素/θ//ð/ | 推荐明日练习',
    techs: ['话语分析', '错误聚合热力图', '自适应推荐算法'],
  },
]

const techCards = [
  {
    title: '语音技术栈', desc: '从音频采集到音素评分，毫秒级实时处理',
    icon: 'Microphone', color: 'var(--color-success)',
    items: ['Whisper 语音识别', 'VAD 静音检测', 'GOP 发音评分', '音素强制对齐', '实时流式推理'],
  },
  {
    title: 'NLP 理解引擎', desc: '语义理解、语法纠错、内容质量评估',
    icon: 'Cpu', color: 'var(--color-primary)',
    items: ['GECToR 语法纠错', 'BERT 语义相似度', 'LLM 意图识别', '文本特征提取', '难易度评估'],
  },
  {
    title: '推荐与调度', desc: '千人千面的自适应学习路径',
    icon: 'Guide', color: 'var(--color-warning)',
    items: ['协同过滤', '强化学习规划', '错误模式追踪', '能力热力图', '自适应题库'],
  },
]

const architecture = [
  { name: '前端展示层', bg: 'rgba(var(--color-primary-rgb), 0.03)', items: ['Vue 3 + Element Plus', 'ECharts 图表', 'Canvas 波形', 'VAD 录音'] },
  { name: 'API 网关层', bg: 'rgba(var(--color-success-rgb), 0.03)', items: ['FastAPI', 'JWT 鉴权', 'WebSocket 流式', '请求限流'] },
  { name: 'AI 推理层', bg: 'rgba(var(--color-warning-rgb), 0.03)', items: ['Whisper ASR', 'GOP/GEC 评分', 'DeepSeek LLM', 'TTS 合成'] },
  { name: '数据服务层', bg: 'rgba(var(--color-danger-rgb), 0.03)', items: ['MySQL', 'Redis 缓存', '音频存储', '日志分析'] },
]
</script>

<template>
  <div class="intro-page">
    <!-- 顶部导航栏 -->
    <header class="landing-header">
      <h1 class="landing-logo">Lingolab</h1>
      <div class="landing-actions">
        <a
          href="https://github.com/xiongchaoyong/Lingolab-ai"
          target="_blank"
          class="github-link"
          title="GitHub 仓库"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
        </a>
        <el-button text @click="router.push('/login')">登录</el-button>
        <el-button type="primary" @click="router.push('/register')">免费注册</el-button>
      </div>
    </header>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-badge">AI · NLP · EdTech</div>
      <h1 class="hero-title">
        用 <span class="gradient-text">AI</span> 重新定义<br />英语口语练习
      </h1>
      <p class="hero-desc">
        从语音识别到智能纠音，从对话模拟到个性化推荐——<br />ASR → NLP 评分 → LLM 生成 → TTS 合成，全链路 AI 驱动
      </p>
      <div class="hero-cta">
        <el-button type="primary" size="large" @click="router.push('/register')">免费开始</el-button>
        <el-button size="large" text @click="router.push('/login')">已有账号？登录</el-button>
      </div>
    </section>

    <!-- 核心技术链路 -->
    <section class="pipeline-section">
      <h2 class="section-title">核心技术链路</h2>
      <div class="pipeline">
        <div v-for="(step, i) in pipeline" :key="step.label" class="pipeline-node">
          <div class="pipe-icon" :style="{ background: step.color }">
            <el-icon :size="28"><component :is="step.icon" /></el-icon>
          </div>
          <div class="pipe-label">{{ step.label }}</div>
          <div class="pipe-tech">{{ step.tech }}</div>
          <div v-if="i < pipeline.length - 1" class="pipe-arrow">→</div>
        </div>
      </div>
    </section>

    <!-- 8步学习流程 -->
    <section class="workflow-section">
      <h2 class="section-title">一次完整的学习过程</h2>
      <p class="section-desc">以「商务电话会议」场景为例，8 步走通 AI 口语训练全流程</p>
      <div class="steps">
        <div v-for="(s, i) in steps" :key="i" class="step-card">
          <div class="step-number">{{ i + 1 }}</div>
          <div class="step-body">
            <div class="step-header">
              <h3>{{ s.title }}</h3>
              <el-tag size="small" effect="plain">{{ s.tag }}</el-tag>
            </div>
            <p class="step-scene">{{ s.scene }}</p>
            <div class="step-tech">
              <el-tag v-for="t in s.techs" :key="t" size="small">{{ t }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI 能力矩阵 -->
    <section class="tech-section">
      <h2 class="section-title">AI 能力矩阵</h2>
      <el-row :gutter="16">
        <el-col v-for="card in techCards" :key="card.title" :span="8" :md="8" :sm="12" :xs="24">
          <div class="tech-card" :style="{ borderTopColor: card.color }">
            <div class="tech-card-icon" :style="{ color: card.color }">
              <el-icon :size="28"><component :is="card.icon" /></el-icon>
            </div>
            <h4>{{ card.title }}</h4>
            <p>{{ card.desc }}</p>
            <ul>
              <li v-for="item in card.items" :key="item">{{ item }}</li>
            </ul>
          </div>
        </el-col>
      </el-row>
    </section>

    <!-- 技术架构 -->
    <section class="arch-section">
      <h2 class="section-title">技术架构</h2>
      <div class="arch-layers">
        <div v-for="layer in architecture" :key="layer.name" class="arch-layer" :style="{ background: layer.bg }">
          <div class="layer-label">{{ layer.name }}</div>
          <div class="layer-items">
            <el-tag v-for="item in layer.items" :key="item" size="small" effect="plain">{{ item }}</el-tag>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style lang="scss" scoped>
.intro-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl) var(--spacing-huge);
}

/* Landing Header */
.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-base) 0;
  position: sticky;
  top: 0;
  background: var(--color-bg-primary);
  z-index: 10;
}
.landing-logo {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.5px;
  margin: 0;
}
.landing-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.github-link {
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
  &:hover { color: var(--color-text-primary); }
}

/* Hero */
.hero {
  text-align: center;
  padding: var(--spacing-xxxl) 0 var(--spacing-xxl);
  .hero-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-base);
    background: rgba(var(--color-primary-rgb), 0.08);
    color: var(--color-primary);
    border-radius: 20px;
    font-size: var(--font-size-sm);
    font-weight: 600;
    font-family: var(--font-heading);
    letter-spacing: 1px;
    margin-bottom: var(--spacing-lg);
  }
  .hero-title {
    font-family: var(--font-heading);
    font-size: 42px;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: var(--spacing-lg);
    letter-spacing: -1px;
  }
  .gradient-text {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-success) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-desc {
    color: var(--color-text-secondary);
    font-family: var(--font-body);
    font-size: var(--font-size-lg);
    line-height: 1.8;
  }
  .hero-cta {
    margin-top: var(--spacing-xxl);
    display: flex;
    gap: var(--spacing-md);
    justify-content: center;
  }
}

/* 节标题 */
.section-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xxl);
  font-weight: 700;
  text-align: center;
  margin-bottom: var(--spacing-md);
}
.section-desc {
  text-align: center;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  margin-bottom: var(--spacing-xl);
}

/* 核心链路 */
.pipeline-section { margin-bottom: var(--spacing-huge); }
.pipeline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}
.pipeline-node {
  display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm);
  position: relative; padding: 0 var(--spacing-base); min-width: 140px;
}
.pipe-icon {
  width: 60px; height: 60px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}
.pipe-label { font-family: var(--font-heading); font-weight: 600; font-size: var(--font-size-base); }
.pipe-tech { font-family: var(--font-body); font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.pipe-arrow {
  position: absolute; right: -18px; top: 18px;
  font-size: 24px; color: var(--color-border); font-weight: 300;
}

/* 8步流程 */
.workflow-section { margin-bottom: var(--spacing-huge); }
.steps { display: flex; flex-direction: column; gap: var(--spacing-base); }
.step-card {
  display: flex; gap: var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  transition: all var(--transition-base);
  cursor: default;
  &:hover { box-shadow: var(--shadow-hover); transform: translateX(4px); }
}
.step-number {
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(var(--color-primary-rgb), 0.08);
  color: var(--color-primary);
  font-family: var(--font-heading); font-size: 20px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-body {
  flex: 1;
  .step-header { display: flex; align-items: center; gap: var(--spacing-md); margin-bottom: var(--spacing-sm);
    h3 { font-family: var(--font-heading); font-size: var(--font-size-lg); font-weight: 600; margin: 0; }
  }
  .step-scene { color: var(--color-text-secondary); font-family: var(--font-body); font-size: var(--font-size-base); line-height: 1.7; margin-bottom: var(--spacing-md); }
  .step-tech { display: flex; gap: var(--spacing-sm); flex-wrap: wrap; }
}

/* AI能力矩阵 */
.tech-section { margin-bottom: var(--spacing-huge); }
.tech-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-top: 3px solid;
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  transition: all var(--transition-base);
  cursor: default;
  &:hover { box-shadow: var(--shadow-hover); transform: translateY(-2px); }
  .tech-card-icon { margin-bottom: var(--spacing-md); }
  h4 { font-family: var(--font-heading); font-size: var(--font-size-lg); font-weight: 600; margin-bottom: var(--spacing-sm); }
  p { color: var(--color-text-secondary); font-family: var(--font-body); font-size: var(--font-size-sm); margin-bottom: var(--spacing-md); line-height: 1.6; }
  ul { padding-left: var(--spacing-lg);
    li { font-family: var(--font-body); font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 2;
      &::marker { color: var(--color-primary); }
    }
  }
}

/* 架构概览 */
.arch-section { margin-bottom: var(--spacing-huge); }
.arch-layers { display: flex; flex-direction: column; gap: var(--spacing-base); }
.arch-layer {
  display: flex; align-items: center; gap: var(--spacing-xl);
  padding: var(--spacing-xl); border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
  &:hover { transform: scale(1.01); }
  .layer-label { font-family: var(--font-heading); font-weight: 600; font-size: var(--font-size-base); white-space: nowrap; min-width: 120px; }
  .layer-items { display: flex; gap: var(--spacing-sm); flex-wrap: wrap; }
}
</style>
