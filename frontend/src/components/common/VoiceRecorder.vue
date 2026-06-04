<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  prepTime: { type: Number, default: 15 },
  maxDuration: { type: Number, default: 45 },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['start', 'stop', 'complete'])

// idle → preparing → recording → scored
const state = ref('idle')
const countdown = ref(0)
const elapsed = ref(0)
let timer = null

const stateLabel = computed(() => ({
  idle: '点击开始录音',
  preparing: `准备中... ${countdown.value}s`,
  recording: '录音中... 点击停止',
  scored: '评分完成',
})[state.value])

const buttonClass = computed(() => `recorder-btn state-${state.value}`)

function startRecording() {
  if (props.disabled) return
  state.value = 'preparing'
  countdown.value = props.prepTime
  emit('start')
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      state.value = 'recording'
      elapsed.value = 0
      timer = setInterval(() => {
        elapsed.value++
        if (elapsed.value >= props.maxDuration) {
          stopRecording()
        }
      }, 1000)
    }
  }, 1000)
}

function stopRecording() {
  clearInterval(timer)
  if (state.value === 'recording') {
    emit('stop', { elapsed: elapsed.value })
    // 模拟评分延迟
    setTimeout(() => {
      state.value = 'scored'
      emit('complete', { elapsed: elapsed.value })
    }, 500)
  } else if (state.value === 'preparing') {
    state.value = 'idle'
  }
}

function reset() {
  clearInterval(timer)
  state.value = 'idle'
  countdown.value = 0
  elapsed.value = 0
}

defineExpose({ reset })
</script>

<template>
  <div class="voice-recorder">
    <div
      :class="buttonClass"
      @click="state === 'idle' || state === 'scored' ? startRecording() : stopRecording()"
    >
      <el-icon :size="state === 'recording' || state === 'preparing' ? 28 : 36">
        <Microphone v-if="state === 'idle' || state === 'scored'" />
        <VideoPause v-else />
      </el-icon>
    </div>
    <p class="recorder-label">{{ stateLabel }}</p>
    <p v-if="state === 'recording'" class="recorder-timer">
      {{ String(Math.floor(elapsed / 60)).padStart(2, '0') }}:{{
        String(elapsed % 60).padStart(2, '0')
      }}
      / {{ String(Math.floor(maxDuration / 60)).padStart(2, '0') }}:{{
        String(maxDuration % 60).padStart(2, '0')
      }}
    </p>
  </div>
</template>

<style lang="scss" scoped>
.voice-recorder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.recorder-btn {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 3px solid var(--color-border);

  &.state-idle {
    background: var(--color-primary);
    color: #fff;
    box-shadow: 0 4px 16px rgba(var(--color-primary-rgb), 0.3);

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 20px rgba(var(--color-primary-rgb), 0.4);
    }
  }

  &.state-preparing {
    background: var(--color-warning);
    color: #fff;
    animation: pulse 1s infinite;
  }

  &.state-recording {
    background: var(--color-danger);
    color: #fff;
    animation: pulse 0.8s infinite;
  }

  &.state-scored {
    background: var(--color-success);
    color: #fff;
  }
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--color-danger-rgb), 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(var(--color-danger-rgb), 0); }
}

.recorder-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.recorder-timer {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}
</style>
