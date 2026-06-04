<script setup>
import { ref, computed } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import DimensionBars from '@/components/common/DimensionBars.vue'

// Mock 数据
const MOCK_WORDS = {
  A1: [
    { word: 'apple', ipa: '/ˈæp.əl/', chinese: '苹果', audio: null },
    { word: 'hello', ipa: '/həˈloʊ/', chinese: '你好', audio: null },
    { word: 'water', ipa: '/ˈwɔː.tər/', chinese: '水', audio: null },
    { word: 'family', ipa: '/ˈfæm.əl.i/', chinese: '家庭', audio: null },
  ],
  A2: [
    { word: 'restaurant', ipa: '/ˈres.trɒnt/', chinese: '餐厅', audio: null },
    { word: 'beautiful', ipa: '/ˈbjuː.tɪ.fəl/', chinese: '美丽的', audio: null },
  ],
  B1: [
    { word: 'environment', ipa: '/ɪnˈvaɪ.rən.mənt/', chinese: '环境', audio: null },
    { word: 'technology', ipa: '/tekˈnɒl.ə.dʒi/', chinese: '科技', audio: null },
  ],
  B2: [
    { word: 'sophisticated', ipa: '/səˈfɪs.tɪ.keɪ.tɪd/', chinese: '精密的', audio: null },
    { word: 'entrepreneur', ipa: '/ˌɒn.trə.prəˈnɜːr/', chinese: '企业家', audio: null },
  ],
}

const MOCK_SENTENCES = {
  A1: [
    { text: 'I like to play football.', chinese: '我喜欢踢足球。' },
    { text: 'She has a big family.', chinese: '她有一个大家庭。' },
  ],
  A2: [
    { text: 'Could you tell me how to get to the station?', chinese: '你能告诉我怎么去车站吗？' },
  ],
  B1: [
    { text: 'The environment is a topic that concerns everyone.', chinese: '环境是每个人都关心的话题。' },
  ],
  B2: [
    { text: 'The sophisticated technology revolutionized the industry.', chinese: '这项精密技术彻底改变了这个行业。' },
  ],
}

// 状态
const mode = ref('word') // word | sentence
const difficulty = ref('A1')
const contentIndex = ref(0)
const recorderRef = ref(null)
const hasScored = ref(false)
const scoreResult = ref(null)

const difficultyOptions = ['A1', 'A2', 'B1', 'B2']

const currentItem = computed(() => {
  if (mode.value === 'word') {
    const words = MOCK_WORDS[difficulty.value] || MOCK_WORDS.A1
    return words[contentIndex.value % words.length]
  } else {
    const sentences = MOCK_SENTENCES[difficulty.value] || MOCK_SENTENCES.A1
    return sentences[contentIndex.value % sentences.length]
  }
})

const isWordMode = computed(() => mode.value === 'word')

function switchMode(newMode) {
  mode.value = newMode
  contentIndex.value = 0
  hasScored.value = false
  scoreResult.value = null
  recorderRef.value?.reset()
}

function handleDifficultyChange() {
  contentIndex.value = 0
  hasScored.value = false
  scoreResult.value = null
  recorderRef.value?.reset()
}

function handleRecordComplete() {
  // Mock 评分结果
  if (isWordMode.value) {
    scoreResult.value = {
      overall: randomScore(55, 92),
      dimensions: [
        { label: '音素准确度', score: randomScore(50, 95) },
        { label: '重音位置', score: randomScore(55, 90) },
        { label: '节奏感', score: randomScore(50, 90) },
      ],
      errors: [
        { phoneme: 'æ', actual: '/æ/ → /e/', tip: '舌尖抵下齿，舌前部向硬腭抬起，口型张大' },
      ],
    }
  } else {
    scoreResult.value = {
      overall: randomScore(50, 90),
      dimensions: [
        { label: '音素准确度', score: randomScore(50, 90) },
        { label: '重音位置', score: randomScore(55, 90) },
        { label: '连读表现', score: randomScore(45, 85) },
        { label: '语调曲线', score: randomScore(50, 88) },
        { label: '节奏感', score: randomScore(50, 90) },
      ],
      errors: [
        { phoneme: 'θ', actual: '/θ/ → /s/', tip: '舌尖轻触上齿，气流从齿缝挤出' },
        { phoneme: 'r', actual: '/r/ → /l/', tip: '舌尖卷起靠近上颚，不要接触' },
      ],
    }
  }
  hasScored.value = true
}

function nextContent() {
  contentIndex.value++
  hasScored.value = false
  scoreResult.value = null
  recorderRef.value?.reset()
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function randomScore(min, max) {
  return Math.round(min + Math.random() * (max - min))
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">AI 发音评测</h2>

    <!-- 模式切换 -->
    <div class="control-bar">
      <el-radio-group v-model="mode" @change="switchMode" size="large">
        <el-radio-button value="word">单词模式</el-radio-button>
        <el-radio-button value="sentence">句子模式</el-radio-button>
      </el-radio-group>

      <div class="control-right">
        <span class="control-label">难度筛选：</span>
        <el-select
          v-model="difficulty"
          @change="handleDifficultyChange"
          style="width: 100px"
          size="small"
        >
          <el-option v-for="d in difficultyOptions" :key="d" :label="d" :value="d" />
        </el-select>
      </div>
    </div>

    <!-- 跟读内容卡片 -->
    <div class="content-display">
      <div class="content-main">
        <span v-if="isWordMode" class="word-text">{{ currentItem.word }}</span>
        <span v-else class="sentence-text">{{ currentItem.text }}</span>
      </div>
      <div v-if="isWordMode" class="content-ipa">{{ currentItem.ipa }}</div>
      <div class="content-chinese">{{ currentItem.chinese }}</div>
      <el-button size="small" text type="primary" class="play-btn">
        <el-icon><VideoPlay /></el-icon> 播放标准音
      </el-button>
    </div>

    <!-- 录音区域 -->
    <div class="record-section" v-if="!hasScored">
      <VoiceRecorder
        ref="recorderRef"
        :prep-time="3"
        :max-duration="isWordMode ? 10 : 30"
        @complete="handleRecordComplete"
      />
    </div>

    <!-- 评分结果 -->
    <div v-if="hasScored && scoreResult" class="score-section">
      <div class="score-divider">
        <span>评分结果</span>
      </div>

      <!-- 综合分 -->
      <div class="overall-score" :style="{ color: getScoreColor(scoreResult.overall) }">
        <span class="overall-number">{{ scoreResult.overall }}</span>
        <span class="overall-unit">分</span>
        <el-tag
          :type="scoreResult.overall >= 80 ? 'success' : scoreResult.overall >= 60 ? 'warning' : 'danger'"
          size="small"
        >
          {{ scoreResult.overall >= 80 ? '优秀' : scoreResult.overall >= 60 ? '良好' : '需加强' }}
        </el-tag>
      </div>

      <!-- 五维评分 -->
      <DimensionBars :dimensions="scoreResult.dimensions" />

      <!-- 错误音素 -->
      <div class="error-section">
        <h4>错误音素定位</h4>
        <div v-for="err in scoreResult.errors" :key="err.phoneme" class="error-item">
          <div class="error-phoneme">
            <el-tag type="danger" size="small">{{ err.phoneme }}</el-tag>
            <span class="error-actual">{{ err.actual }}</span>
          </div>
          <p class="error-tip">
            <el-icon><InfoFilled /></el-icon>
            {{ err.tip }}
          </p>
        </div>
      </div>

      <!-- 下一题 -->
      <el-button type="primary" @click="nextContent" style="width: 100%;">
        下一个
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.control-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.control-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

// 跟读内容
.content-display {
  background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.04), rgba(var(--color-primary-rgb), 0.08));
  border: 1px solid rgba(var(--color-primary-rgb), 0.15);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xxl);
  text-align: center;
  margin-bottom: var(--spacing-xxl);
}

.content-main {
  margin-bottom: var(--spacing-sm);

  .word-text {
    font-size: 36px;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  .sentence-text {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.6;
  }
}

.content-ipa {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  font-family: 'Segoe UI', serif;
}

.content-chinese {
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-md);
}

.play-btn {
  margin-top: var(--spacing-sm);
}

// 录音区域
.record-section {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xxl) 0;
}

// 评分结果
.score-section {
  margin-top: var(--spacing-xl);
}

.score-divider {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);

  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--color-border);
  }
}

.overall-score {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xl);

  .overall-number {
    font-size: 48px;
    font-weight: 800;
    line-height: 1;
  }

  .overall-unit {
    font-size: var(--font-size-lg);
    margin-right: var(--spacing-sm);
  }
}

// 错误音素
.error-section {
  margin: var(--spacing-xl) 0;
  padding: var(--spacing-lg);
  background: rgba(var(--color-danger-rgb), 0.04);
  border: 1px solid rgba(var(--color-danger-rgb), 0.12);
  border-radius: var(--radius-md);

  h4 {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: var(--spacing-md);
  }
}

.error-item {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);

  &:last-child {
    margin-bottom: 0;
  }
}

.error-phoneme {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.error-actual {
  font-size: var(--font-size-base);
  color: var(--color-danger);
  font-family: 'Segoe UI', monospace;
}

.error-tip {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
}
</style>
