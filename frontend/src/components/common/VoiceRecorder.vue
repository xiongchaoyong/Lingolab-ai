<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  prepTime: { type: Number, default: 3 },
  maxDuration: { type: Number, default: 45 },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['start', 'stop', 'complete'])

const state = ref('idle') // idle → preparing → recording → uploading → scored
const countdown = ref(0)
const elapsed = ref(0)
let timer = null
let mediaRecorder = null
let audioChunks = []
let audioBlob = null
let stream = null

const stateLabel = computed(() => ({
  idle: '点击开始录音',
  preparing: `准备中... ${countdown.value}s`,
  recording: '录音中... 点击停止',
  uploading: '评分中...',
  scored: '评分完成',
})[state.value])

const buttonClass = computed(() => `recorder-btn state-${state.value}`)

async function startRecording() {
  if (props.disabled) return

  // 请求麦克风权限
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: 16000, channelCount: 1 }
    })
  } catch (e) {
    console.error('麦克风访问失败:', e)
    return
  }

  state.value = 'preparing'
  countdown.value = props.prepTime
  audioChunks = []
  audioBlob = null
  emit('start')

  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      beginCapture()
    }
  }, 1000)
}

function beginCapture() {
  // 不指定 mimeType，让浏览器选择默认格式（通常 audio/webm;codecs=opus）
  mediaRecorder = new MediaRecorder(stream)
  audioChunks = []

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data)
  }

  mediaRecorder.onstop = () => {
    // 释放麦克风
    stream.getTracks().forEach(t => t.stop())
    const actualMime = mediaRecorder.mimeType || mimeType
    audioBlob = new Blob(audioChunks, { type: actualMime })

    // 通知父组件
    state.value = 'uploading'
    emit('complete', {
      blob: audioBlob,
      mimeType: actualMime,
      elapsed: elapsed.value,
    })
  }

  mediaRecorder.start()
  state.value = 'recording'
  elapsed.value = 0
  timer = setInterval(() => {
    elapsed.value++
    if (elapsed.value >= props.maxDuration) {
      stopRecording()
    }
  }, 1000)
}

function stopRecording() {
  clearInterval(timer)
  if (state.value === 'preparing') {
    stream?.getTracks().forEach(t => t.stop())
    state.value = 'idle'
  } else if (state.value === 'recording' && mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
}

function setScored() {
  state.value = 'scored'
}

function reset() {
  clearInterval(timer)
  stream?.getTracks().forEach(t => t.stop())
  state.value = 'idle'
  countdown.value = 0
  elapsed.value = 0
  audioChunks = []
  audioBlob = null
}

defineExpose({ reset, setScored })
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

  &.state-uploading {
    background: var(--color-primary);
    color: #fff;
    opacity: 0.7;
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
