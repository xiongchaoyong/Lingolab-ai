<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'

const router = useRouter()
const store = useAssessmentStore()

const selectedOption = ref(null)
const showResult = ref(false)
const isCorrect = ref(false)
const timerSeconds = ref(0)
let timer = null

onMounted(() => {
  store.startAssessment()
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
  const correct = store.currentQuestion.answer
  isCorrect.value = selectedOption.value === correct
  showResult.value = true
}

// 口语题 — 录音完成
function handleSpeakingComplete() {
  store.saveAnswer('spoken_answer')
  isCorrect.value = true // 口语不判对错
  showResult.value = true
}

// 下一题
function handleNext() {
  showResult.value = false
  selectedOption.value = null
  if (store.isLastQuestion) {
    store.completeAssessment()
    router.push('/assessment/result')
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
          :disabled="showResult"
        >
          <div
            v-for="opt in store.currentQuestion?.options"
            :key="opt[0]"
            class="option-item"
            :class="{
              'is-selected': selectedOption === opt[0],
              'is-correct': showResult && opt[0] === store.currentQuestion?.answer,
              'is-wrong': showResult && selectedOption === opt[0] && opt[0] !== store.currentQuestion?.answer,
            }"
          >
            <el-radio :label="opt[0]" :value="opt[0]" size="large">
              {{ opt }}
            </el-radio>
          </div>
        </el-radio-group>

        <!-- 结果显示 -->
        <div v-if="showResult" class="result-feedback" :class="isCorrect ? 'correct' : 'wrong'">
          <el-icon :size="20">
            <CircleCheckFilled v-if="isCorrect" />
            <CircleCloseFilled v-else />
          </el-icon>
          <span>{{ isCorrect ? '回答正确！' : `正确答案是 ${store.currentQuestion?.answer}` }}</span>
        </div>
      </template>

      <!-- 口语题 -->
      <template v-else>
        <div class="speaking-area">
          <p class="speaking-prompt">
            <el-icon><InfoFilled /></el-icon>
            请用英语自由表达，录音时长 30-60 秒
          </p>

          <VoiceRecorder
            v-if="!showResult"
            :prep-time="15"
            :max-duration="45"
            @complete="handleSpeakingComplete"
          />

          <div v-if="showResult" class="result-feedback correct">
            <el-icon :size="20"><CircleCheckFilled /></el-icon>
            <span>录音已提交，AI 正在评分...</span>
          </div>
        </div>
      </template>
    </div>

    <!-- 底部操作栏 -->
    <div class="assessment-footer">
      <template v-if="!showResult">
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
      </template>
      <template v-else>
        <el-button type="primary" size="large" @click="handleNext">
          {{ store.isLastQuestion ? '查看测评结果' : '下一题' }}
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </template>

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

  &.is-correct {
    border-color: var(--color-success);
    background: rgba(var(--color-success-rgb), 0.08);
  }

  &.is-wrong {
    border-color: var(--color-danger);
    background: rgba(var(--color-danger-rgb), 0.08);
  }

  :deep(.el-radio) {
    width: 100%;
  }
}

// 结果反馈
.result-feedback {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;

  &.correct {
    background: rgba(var(--color-success-rgb), 0.1);
    color: var(--color-success);
  }

  &.wrong {
    background: rgba(var(--color-danger-rgb), 0.1);
    color: var(--color-danger);
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
