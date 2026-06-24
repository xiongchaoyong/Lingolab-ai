<script setup>
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import DimensionBars from '@/components/common/DimensionBars.vue'

const router = useRouter()
const store = useAssessmentStore()

const report = computed(() => store.report)

const dimensionList = computed(() => {
  if (!report.value) return []
  const labels = { listening: '听力理解', speaking: '口语表达', reading: '阅读理解', grammar: '语法选择' }
  return Object.entries(report.value.dimensionScores).map(([key, score]) => ({
    label: labels[key] || key,
    score,
    maxScore: 100,
  }))
})

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
</style>
