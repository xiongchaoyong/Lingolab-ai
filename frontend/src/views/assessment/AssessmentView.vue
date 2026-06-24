<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAssessmentStore } from '@/stores/assessment'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'

const router = useRouter()
const store = useAssessmentStore()

const selectedOption = ref(null)
const timerSeconds = ref(0)
let timer = null

onMounted(async () => {
  await store.startAssessment()
  startTimer()
})

onUnmounted(() => clearInterval(timer))

function startTimer() {
  const elapsed = store.startTime ? Math.floor((Date.now() - store.startTime) / 1000) : 0
  timerSeconds.value = elapsed
  timer = setInterval(() => { timerSeconds.value++ }, 1000)
}

const formattedTime = computed(() => {
  const m = Math.floor(timerSeconds.value / 60)
  const s = timerSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const estimatedTime = computed(() => {
  const remain = store.totalQuestions - store.currentIndex
  const m = Math.floor(remain * 1.0)
  return `预计剩余 ${m} 分钟`
})

// 客观题 — 提交答案
function handleSubmitOption() {
  if (!selectedOption.value && !store.isSpeakingQuestion) return
  store.saveAnswer(selectedOption.value)
  handleNext()
}

// 口语题 — 录音完成
function handleSpeakingComplete() {
  store.saveAnswer('spoken_answer')
  handleNext()
}

// 下一题
async function handleNext() {
  selectedOption.value = null
  if (store.isLastQuestion) {
    try {
      await store.completeAssessment()
      router.push('/assessment/result')
    } catch (e) {
      console.error('提交测评失败:', e)
      ElMessage.error('提交失败，请检查网络后重试')
    }
  } else {
    store.nextQuestion()
  }
}

// 退出测评
function handleExit() {
  store.saveProgress()
  router.push('/home')
}

// 提前结束（口语跳过）
function handleSkip() {
  store.saveAnswer('skipped')
  handleNext()
}
</script>

<template>
  <div class="assessment-page">
    <!-- 顶栏 -->
    <div class="assessment-topbar">
      <el-button text @click="handleExit">
        <el-icon><ArrowLeft /></el-icon> 退出
      </el-button>
      <span class="question-progress">
        第 {{ store.currentIndex + 1 }} / {{ store.totalQuestions }} 题
      </span>
      <span class="timer">{{ formattedTime }}</span>
    </div>

    <!-- 进度条 -->
    <el-progress
      :percentage="store.progress"
      :stroke-width="3"
      :show-text="false"
      color="var(--color-primary)"
    />

    <!-- 题目内容 -->
    <div class="question-body">
      <!-- 题目标签 -->
      <div class="question-tags">
        <el-tag :type="store.difficultyColor" size="small">
          {{ store.currentQuestion?.difficulty }} 难度
        </el-tag>
        <el-tag type="info" size="small">{{ store.typeLabel }}</el-tag>
      </div>

      <!-- 题目文本 -->
      <div class="question-text">{{ store.currentQuestion?.content }}</div>

      <!-- 客观题：选择题 -->
      <template v-if="!store.isSpeakingQuestion">
        <el-radio-group
          v-model="selectedOption"
          class="options-group"
        >
          <div
            v-for="opt in store.currentQuestion?.options"
            :key="opt[0]"
            class="option-item"
            :class="{
              'is-selected': selectedOption === opt[0],
            }"
          >
            <el-radio :label="opt[0]" :value="opt[0]" size="large">
              {{ opt }}
            </el-radio>
          </div>
        </el-radio-group>
      </template>

      <!-- 口语题 -->
      <template v-else>
        <div class="speaking-area">
          <p class="speaking-prompt">
            <el-icon><InfoFilled /></el-icon>
            请用英语自由表达，录音时长 30-60 秒
          </p>

          <VoiceRecorder
            :prep-time="3"
            :max-duration="45"
            @complete="handleSpeakingComplete"
          />
        </div>
      </template>
    </div>

    <!-- 底部操作栏 -->
    <div class="assessment-footer">
      <el-button
        v-if="!store.isSpeakingQuestion"
        type="primary"
        size="large"
        :disabled="!selectedOption"
        @click="handleSubmitOption"
      >
        确认答案
      </el-button>
      <el-button
        v-if="store.isSpeakingQuestion"
        text
        type="info"
        size="small"
        @click="handleSkip"
      >
        跳过此题
      </el-button>

      <p class="time-estimate">{{ estimatedTime }}</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.assessment-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

// 顶栏
.assessment-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);

  .question-progress {
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .timer {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--color-primary);
    font-variant-numeric: tabular-nums;
  }
}

// 题目内容
.question-body {
  flex: 1;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  padding: var(--spacing-xxxl) var(--spacing-xl);
  overflow-y: auto;
}

.question-tags {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
}

.question-text {
  font-size: var(--font-size-lg);
  line-height: 1.8;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xxl);
  white-space: pre-line;
  background: var(--color-bg-secondary);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-primary);
}

// 选项
.options-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  width: 100%;
}

.option-item {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.2s;

  &.is-selected {
    border-color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.05);
  }

  :deep(.el-radio) {
    width: 100%;
  }
}

// 口语区域
.speaking-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xxl);
  padding: var(--spacing-xxxl) 0;

  .speaking-prompt {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }
}

// 底部
.assessment-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg) var(--spacing-xl) var(--spacing-xxl);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);

  .time-estimate {
    font-size: var(--font-size-sm);
    color: var(--color-text-disabled);
  }
}
</style>
