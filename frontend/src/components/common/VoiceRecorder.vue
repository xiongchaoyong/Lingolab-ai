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
let audioBlob = null
let stream = null

// Web Audio API 相关
let audioContext = null
let scriptProcessor = null
let mediaStreamSource = null
let pcmChunks = []
let sampleRate = 16000

const stateLabel = computed(() => ({
  idle: '点击开始录音',
  preparing: `准备中... ${countdown.value}s`,
  recording: '录音中... 点击停止',
  uploading: '评分中...',
  scored: '评分完成',
})[state.value])

const buttonClass = computed(() => `recorder-btn state-${state.value}`)

// ===== WAV 编码工具函数 =====

function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  // RIFF header
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeString(view, 8, 'WAVE')
  // fmt chunk
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)        // chunk size
  view.setUint16(20, 1, true)         // PCM format
  view.setUint16(22, 1, true)         // mono
  view.setUint32(24, sampleRate, true) // sample rate
  view.setUint32(28, sampleRate * 2, true) // byte rate
  view.setUint16(32, 2, true)         // block align
  view.setUint16(34, 16, true)        // bits per sample
  // data chunk
  writeString(view, 36, 'data')
  view.setUint32(40, samples.length * 2, true)

  // PCM samples
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i))
  }
}

function floatTo16BitPCM(float32Array) {
  const buffer = new Int16Array(float32Array.length)
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return buffer
}

async function startRecording() {
  if (props.disabled) return

  // 请求麦克风权限
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: { ideal: 16000 }, channelCount: 1 }
    })
  } catch (e) {
    console.error('麦克风访问失败:', e)
    return
  }

  state.value = 'preparing'
  countdown.value = props.prepTime
  pcmChunks = []
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
  // 使用 Web Audio API 捕获 PCM 数据
  audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
  sampleRate = audioContext.sampleRate
  mediaStreamSource = audioContext.createMediaStreamSource(stream)

  // 使用 ScriptProcessorNode 捕获原始 PCM
  scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1)
  pcmChunks = []

  scriptProcessor.onaudioprocess = (e) => {
    const inputData = e.inputBuffer.getChannelData(0)
    // 复制 Float32Array 数据
    pcmChunks.push(new Float32Array(inputData))
  }

  mediaStreamSource.connect(scriptProcessor)
  scriptProcessor.connect(audioContext.destination)

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
  } else if (state.value === 'recording') {
    // 断开音频处理
    scriptProcessor?.disconnect()
    mediaStreamSource?.disconnect()
    audioContext?.close()
    stream?.getTracks().forEach(t => t.stop())

    // 合并所有 PCM 数据
    const totalLength = pcmChunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const merged = new Float32Array(totalLength)
    let offset = 0
    for (const chunk of pcmChunks) {
      merged.set(chunk, offset)
      offset += chunk.length
    }

    // 编码为 WAV
    audioBlob = encodeWAV(merged, sampleRate)

    state.value = 'uploading'
    emit('complete', {
      blob: audioBlob,
      mimeType: 'audio/wav',
      elapsed: elapsed.value,
    })
  }
}

function setScored() {
  state.value = 'scored'
}

function reset() {
  clearInterval(timer)
  stream?.getTracks().forEach(t => t.stop())
  scriptProcessor?.disconnect()
  mediaStreamSource?.disconnect()
  audioContext?.close()
  state.value = 'idle'
  countdown.value = 0
  elapsed.value = 0
  pcmChunks = []
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
