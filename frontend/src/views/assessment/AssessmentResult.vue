<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import DimensionBars from '@/components/common/DimensionBars.vue'

const router = useRouter()
const store = useAssessmentStore()

const report = computed(() => store.report)
const showDetail = ref(false)

const dimensionList = computed(() => {
  if (!report.value) return []
  const labels = { speaking: '口语表达', reading: '阅读理解', grammar: '语法选择' }
  return Object.entries(report.value.dimensionScores).map(([key, score]) => ({
    label: labels[key] || key,
    score,
    maxScore: 100,
  }))
})

const questionsDetail = computed(() => report.value?.questionsDetail || [])

const correctCount = computed(() => questionsDetail.value.filter(q => q.is_correct).length)
const wrongCount = computed(() => questionsDetail.value.filter(q => q.is_correct === false).length)
const speakingCount = computed(() => questionsDetail.value.filter(q => q.type === 'speaking').length)

const scoreColor = computed(() => {
  const s = report.value?.overall || 0
  if (s >= 80) return 'var(--color-success)'
  if (s >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
})

const levelColorMap = {
  A1: 'var(--color-info)', A2: 'var(--color-success)',
  B1: 'var(--color-warning)', B2: 'var(--color-warning)',
  C1: 'var(--color-danger)', C2: 'var(--color-danger)',
}

const difficultyColorMap = {
  A1: 'info', A2: 'success', B1: 'warning', B2: 'warning', C1: 'danger', C2: 'danger',
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function handleGoHome() {
  router.push('/home')
}

onMounted(() => {
  if (!store.report) {
    router.push('/')
  }
})
</script>

<template>
  <div class="immersive-layout" style="padding: 40px 0;">
    <div class="immersive-card" style="max-width: 560px;">
      <!-- 标题 -->
      <div class="result-header">
        <el-icon :size="48" color="var(--color-success)"><CircleCheckFilled /></el-icon>
        <h2>测评完成！</h2>
        <p class="result-duration">
          用时 {{ Math.floor((report?.duration || 0) / 60) }} 分 {{ (report?.duration || 0) % 60 }} 秒
        </p>
      </div>

      <!-- CEFR 等级徽章 -->
      <div class="level-badge" v-if="report">
        <div class="level-circle" :style="{ borderColor: levelColorMap[report.cefrLevel.level] || '#999' }">
          <span class="level-text">{{ report.cefrLevel.level }}</span>
        </div>
        <span class="level-label">{{ report.cefrLevel.label }}</span>
        <span class="level-overall" :style="{ color: scoreColor }">
          {{ report.overall }} 分
        </span>
      </div>

      <!-- 维度得分 -->
      <div class="dimension-section" v-if="report">
        <h3 class="section-title">各维度得分</h3>
        <DimensionBars :dimensions="dimensionList" />
      </div>

      <!-- 答题概况 -->
      <div class="summary-row" v-if="questionsDetail.length > 0">
        <div class="summary-item success">
          <span class="summary-num">{{ correctCount }}</span>
          <span class="summary-label">正确</span>
        </div>
        <div class="summary-item danger">
          <span class="summary-num">{{ wrongCount }}</span>
          <span class="summary-label">错误</span>
        </div>
        <div class="summary-item info" v-if="speakingCount > 0">
          <span class="summary-num">{{ speakingCount }}</span>
          <span class="summary-label">口语</span>
        </div>
      </div>

      <!-- 逐题详情 -->
      <div class="detail-section" v-if="questionsDetail.length > 0">
        <div class="detail-header" @click="showDetail = !showDetail">
          <h3 class="section-title">答题详情 ({{ questionsDetail.length }} 题)</h3>
          <el-icon :class="{ rotated: showDetail }"><ArrowDown /></el-icon>
        </div>

        <div class="detail-list" v-show="showDetail">
          <div
            v-for="q in questionsDetail"
            :key="q.order"
            class="detail-item"
            :class="{
              'item-correct': q.is_correct === true,
              'item-wrong': q.is_correct === false,
              'item-speaking': q.type === 'speaking',
            }"
          >
            <div class="item-top">
              <span class="item-order">#{{ q.order }}</span>
              <el-tag :type="difficultyColorMap[q.difficulty] || 'info'" size="small">
                {{ q.difficulty }}
              </el-tag>
              <span class="item-type">{{ q.type_label }}</span>
              <span class="item-score" :style="{ color: getScoreColor(q.score) }">
                {{ q.score }}分
              </span>
            </div>
            <div class="item-content" v-if="q.content">{{ q.content }}</div>
            <div class="item-answer-row" v-if="q.type !== 'speaking'">
              <span class="answer-label">你的答案：</span>
              <span :class="q.is_correct ? 'answer-ok' : 'answer-err'">{{ q.user_answer || '未答' }}</span>
              <span v-if="!q.is_correct && q.correct_answer" class="correct-hint">
                → 正确答案：{{ q.correct_answer }}
              </span>
            </div>
            <div class="item-transcript" v-if="q.transcript">
              <span class="answer-label">转写：</span>{{ q.transcript }}
            </div>
          </div>
        </div>
      </div>

      <!-- 短板建议 -->
      <div class="suggestion-box" v-if="report">
        <p class="suggestion-title">
          <el-icon><WarningFilled /></el-icon>
          短板：{{ report.weakness.label }}
        </p>
        <p class="suggestion-text">{{ report.weakness.suggestion }}</p>
      </div>

      <!-- 操作按钮 -->
      <el-button type="primary" size="large" class="enter-btn" @click="handleGoHome">
        进入首页开始学习
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.result-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);

  h2 {
    font-size: var(--font-size-xl);
    margin: var(--spacing-md) 0 var(--spacing-sm);
    color: var(--color-text-primary);
  }

  .result-duration {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }
}

.level-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--spacing-xxl);
}

.level-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 4px solid var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-sm);

  .level-text {
    font-size: 32px;
    font-weight: 800;
    color: var(--color-text-primary);
  }
}

.level-label {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.level-overall {
  font-size: 28px;
  font-weight: 800;
  margin-top: var(--spacing-sm);
}

.dimension-section {
  margin-bottom: var(--spacing-xl);

  .section-title {
    font-size: var(--font-size-base);
    font-weight: 600;
    margin-bottom: var(--spacing-lg);
    color: var(--color-text-primary);
  }
}

.suggestion-box {
  background: rgba(var(--color-warning-rgb), 0.08);
  border: 1px solid rgba(var(--color-warning-rgb), 0.2);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);

  .suggestion-title {
    font-weight: 600;
    color: var(--color-warning);
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-sm);
  }

  .suggestion-text {
    color: var(--color-text-secondary);
    line-height: 1.6;
    font-size: var(--font-size-sm);
  }
}

.enter-btn {
  width: 100%;
}

.summary-row {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.summary-item {
  flex: 1;
  text-align: center;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;

  .summary-num {
    font-size: 28px;
    font-weight: 800;
  }
  .summary-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin-top: 2px;
  }
}

.summary-item.success {
  background: rgba(var(--color-success-rgb), 0.1);
  .summary-num { color: var(--color-success); }
}
.summary-item.danger {
  background: rgba(var(--color-danger-rgb), 0.1);
  .summary-num { color: var(--color-danger); }
}
.summary-item.info {
  background: rgba(var(--color-info-rgb), 0.1);
  .summary-num { color: var(--color-info); }
}

.detail-section {
  margin-bottom: var(--spacing-xl);

  .section-title {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: var(--spacing-sm) 0;

  .el-icon {
    transition: transform 0.2s;
    &.rotated { transform: rotate(180deg); }
  }
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.detail-item {
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-border);
  background: var(--color-bg-secondary);

  &.item-correct { border-left-color: var(--color-success); }
  &.item-wrong { border-left-color: var(--color-danger); }
  &.item-speaking { border-left-color: var(--color-info); }

  .item-top {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }

  .item-order {
    font-weight: 700;
    color: var(--color-text-primary);
    min-width: 28px;
  }

  .item-type {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }

  .item-score {
    margin-left: auto;
    font-weight: 700;
    font-size: var(--font-size-sm);
  }

  .item-content {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin: var(--spacing-xs) 0;
    line-height: 1.5;
  }

  .item-answer-row {
    font-size: var(--font-size-xs);
    margin-top: var(--spacing-xs);

    .answer-label { color: var(--color-text-secondary); }
    .answer-ok { color: var(--color-success); font-weight: 600; }
    .answer-err { color: var(--color-danger); font-weight: 600; }
    .correct-hint { color: var(--color-success); margin-left: var(--spacing-sm); }
  }

  .item-transcript {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin-top: var(--spacing-xs);
    font-style: italic;
  }
}
</style>
