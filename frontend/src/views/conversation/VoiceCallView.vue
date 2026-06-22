<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { streamStartConversation, streamSpeakConversation, ttsConversation, endConversation } from '@/api/conversation'

const router = useRouter()

// ========== 场景配置 ==========
const SCENARIOS = [
  { id: 'self_intro', title: '自我介绍', subtitle: '聊聊你自己吧', emoji: '👋', color: '#FF6B8A' },
  { id: 'directions', title: '问路指路', subtitle: '帮助迷路的朋友', emoji: '🗺️', color: '#5B8FF9' },
  { id: 'shopping', title: '购物', subtitle: '一起逛街购物', emoji: '🛍️', color: '#F6BD16' },
  { id: 'restaurant', title: '餐厅', subtitle: '享受美食时光', emoji: '🍽️', color: '#5AD8A6' },
]

// ========== 状态 ==========
const phase = ref('select') // select | calling | report
const selectedScenario = ref(null)
const sessionId = ref('')
const callState = ref('idle') // idle | ai_speaking | listening | thinking
const subtitle = ref('')
const userSubtitle = ref('')
const isConnecting = ref(false)
const scoreReport = ref(null)
const isScoring = ref(false)

// 音频相关
let audioContext = null
let analyser = null
let mediaRecorder = null
let audioChunks = []
let silenceTimer = null
let currentAudio = null
const SILENCE_THRESHOLD = 0.02  // 音量阈值
const SILENCE_DURATION = 1500   // 静音 1.5 秒后自动停止

// ========== 场景选择 ==========
async function selectScenario(scenario) {
  selectedScenario.value = scenario
  phase.value = 'calling'
  callState.value = 'idle'
  subtitle.value = ''
  userSubtitle.value = ''

  // 开始对话
  isConnecting.value = true
  streamStartConversation(scenario.id, 'B1', {
    onToken(text) {
      subtitle.value += text
    },
    onDone(data) {
      isConnecting.value = false
      sessionId.value = data.session_id
      subtitle.value = data.full_text
      // 生成 TTS 并播放
      speakAndListen(data.full_text)
    },
    onError() {
      isConnecting.value = false
      subtitle.value = 'Connection failed. Please try again.'
    },
  })
}

// ========== AI 说话 → 自动听 ==========
async function speakAndListen(text) {
  callState.value = 'ai_speaking'
  try {
    const ttsData = await ttsConversation(text)
    const blob = base64ToBlob(ttsData.audio_base64, 'audio/mpeg')
    const url = URL.createObjectURL(blob)
    currentAudio = new Audio(url)
    currentAudio.onended = () => {
      URL.revokeObjectURL(url)
      // AI 说完 → 自动开始听
      startListening()
    }
    currentAudio.onerror = () => {
      // 播放失败，直接开始听
      startListening()
    }
    await currentAudio.play()
  } catch (e) {
    // TTS 失败，直接开始听
    startListening()
  }
}

// ========== VAD 录音 ==========
async function startListening() {
  callState.value = 'listening'
  userSubtitle.value = ''
  audioChunks = []

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: 16000, channelCount: 1 },
    })

    audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop())
      audioContext.close()
      processUserAudio()
    }
    mediaRecorder.start()

    // VAD 检测循环
    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    let silenceStart = null

    function checkVolume() {
      if (callState.value !== 'listening') return
      analyser.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128
        sum += v * v
      }
      const rms = Math.sqrt(sum / dataArray.length)

      if (rms < SILENCE_THRESHOLD) {
        if (!silenceStart) silenceStart = Date.now()
        else if (Date.now() - silenceStart > SILENCE_DURATION) {
          // 静音足够久，停止录音
          if (mediaRecorder?.state === 'recording') {
            mediaRecorder.stop()
          }
          return
        }
      } else {
        silenceStart = null
      }
      requestAnimationFrame(checkVolume)
    }
    requestAnimationFrame(checkVolume)
  } catch (e) {
    console.error('麦克风访问失败:', e)
    callState.value = 'idle'
  }
}

async function processUserAudio() {
  if (audioChunks.length === 0) {
    // 用户没说话，重新开始听
    startListening()
    return
  }

  callState.value = 'thinking'
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })

  streamSpeakConversation(sessionId.value, selectedScenario.value.id, audioBlob, {
    onAsr(text) {
      userSubtitle.value = text
    },
    onToken(text) {
      subtitle.value += text
    },
    onDone(data) {
      subtitle.value = data.full_text
      // AI 回复 → 播放语音
      speakAndListen(data.full_text)
    },
    onError() {
      subtitle.value = 'Sorry, I had trouble understanding that.'
      startListening()
    },
  })
}

// ========== 挂断 ==========
async function hangUp() {
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  if (silenceTimer) clearTimeout(silenceTimer)

  // 获取评分报告
  if (sessionId.value) {
    isScoring.value = true
    try {
      scoreReport.value = await endConversation(sessionId.value)
    } catch (e) {
      scoreReport.value = {
        overall: 0,
        pronunciation: [],
        text_dimensions: [
          { label: '语法正确率', score: 0 },
          { label: '词汇丰富度', score: 0 },
          { label: '对话参与度', score: 0 },
        ],
        suggestions: '评分服务暂时异常，请稍后重试',
      }
    }
    isScoring.value = false
    phase.value = 'report'
  } else {
    phase.value = 'select'
    resetCall()
  }
}

function resetCall() {
  selectedScenario.value = null
  callState.value = 'idle'
  subtitle.value = ''
  userSubtitle.value = ''
  scoreReport.value = null
  sessionId.value = ''
}

function backToScenes() {
  phase.value = 'select'
  resetCall()
}

function goBack() {
  router.push('/home')
}

// ========== 工具函数 ==========
function base64ToBlob(base64, mimeType) {
  const byteChars = atob(base64)
  const byteArrays = []
  for (let offset = 0; offset < byteChars.length; offset += 512) {
    const slice = byteChars.slice(offset, offset + 512)
    const byteNumbers = new Array(slice.length)
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i)
    }
    byteArrays.push(new Uint8Array(byteNumbers))
  }
  return new Blob(byteArrays, { type: mimeType })
}

function dimScoreColor(score) {
  if (score >= 80) return '#5AD8A6'
  if (score >= 60) return '#F6BD16'
  return '#FF6B8A'
}

function dimBarColor(score) {
  if (score >= 80) return 'linear-gradient(90deg, #5AD8A6, #3EC790)'
  if (score >= 60) return 'linear-gradient(90deg, #F6BD16, #F09B00)'
  return 'linear-gradient(90deg, #FF6B8A, #FF8E9E)'
}

onUnmounted(() => {
  hangUp()
})
</script>

<template>
  <div class="voice-call-page">
    <!-- 场景选择 -->
    <template v-if="phase === 'select'">
      <div class="call-select-header">
        <div class="header-mascot">🐱</div>
        <h2>AI 智能对话</h2>
        <p class="select-subtitle">选一个场景，和我一起练习口语吧~</p>
      </div>
      <div class="call-scenario-grid">
        <div
          v-for="scene in SCENARIOS"
          :key="scene.id"
          class="call-scenario-card"
          :style="{ '--accent': scene.color }"
          @click="selectScenario(scene)"
        >
          <div class="csc-emoji">{{ scene.emoji }}</div>
          <h4>{{ scene.title }}</h4>
          <p>{{ scene.subtitle }}</p>
        </div>
      </div>
      <div class="select-footer">
        <el-button text @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon> 返回首页
        </el-button>
      </div>
    </template>

    <!-- 通话界面 -->
    <template v-else-if="phase === 'calling'">
      <div class="call-screen">
        <!-- 顶部装饰 -->
        <div class="call-top">
          <div class="call-scene-pill">
            <span class="pill-emoji">{{ selectedScenario?.emoji }}</span>
            {{ selectedScenario?.title }}
          </div>
        </div>

        <!-- 中间状态区 -->
        <div class="call-center">
          <!-- 可爱头像 + 波纹 -->
          <div class="mascot-container" :class="callState">
            <div class="ripple-ring r1"></div>
            <div class="ripple-ring r2"></div>
            <div class="ripple-ring r3"></div>
            <div class="mascot-avatar">
              <span class="mascot-face">🐱</span>
            </div>
          </div>

          <div class="call-state-label" :class="callState">
            <template v-if="isConnecting">正在连接...</template>
            <template v-else-if="callState === 'ai_speaking'">
              <span class="state-dot speaking"></span> AI 正在说话
            </template>
            <template v-else-if="callState === 'listening'">
              <span class="state-dot listening"></span> 正在聆听...
            </template>
            <template v-else-if="callState === 'thinking'">
              <span class="state-dot thinking"></span> 思考中...
            </template>
            <template v-else>准备就绪</template>
          </div>
        </div>

        <!-- 底部字幕区 -->
        <div class="call-subtitles">
          <div v-if="userSubtitle" class="subtitle user-subtitle">
            <span class="subtitle-avatar">😊</span>
            <span class="subtitle-text">{{ userSubtitle }}</span>
          </div>
          <div v-if="subtitle" class="subtitle ai-subtitle">
            <span class="subtitle-avatar">🐱</span>
            <span class="subtitle-text">{{ subtitle }}</span>
          </div>
        </div>

        <!-- 挂断按钮 -->
        <div class="call-actions">
          <button class="hangup-btn" @click="hangUp">
            <span class="hangup-icon">📞</span>
          </button>
          <p class="hangup-label">点击挂断</p>
        </div>
      </div>
    </template>

    <!-- 评分报告 -->
    <template v-else-if="phase === 'report'">
      <div class="report-screen">
        <div class="report-header">
          <div class="report-mascot">🌟</div>
          <h2>对话报告</h2>
          <p v-if="scoreReport" class="report-scene">
            {{ selectedScenario?.emoji }} {{ selectedScenario?.title }} 场景
          </p>
        </div>

        <div class="report-content" v-if="scoreReport && !isScoring">
          <!-- 综合分 -->
          <div class="overall-circle" :style="{ '--score': scoreReport.overall }">
            <span class="overall-num">{{ scoreReport.overall }}</span>
            <span class="overall-unit">分</span>
            <span class="overall-level">
              {{ scoreReport.overall >= 80 ? '🎉 优秀' : scoreReport.overall >= 60 ? '👍 良好' : '💪 加油' }}
            </span>
          </div>

          <!-- 语音评测维度 -->
          <div class="dimension-group" v-if="scoreReport.pronunciation && scoreReport.pronunciation.length">
            <div class="dim-group-title">
              <span class="group-icon">🎤</span> 语音评测
            </div>
            <div class="dimension-list">
              <div
                v-for="dim in scoreReport.pronunciation"
                :key="dim.label"
                class="dimension-item"
              >
                <div class="dim-header">
                  <span class="dim-label">{{ dim.label }}</span>
                  <span class="dim-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span>
                </div>
                <div class="dim-bar-bg">
                  <div
                    class="dim-bar-fill"
                    :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 文本评测维度 -->
          <div class="dimension-group" v-if="scoreReport.text_dimensions && scoreReport.text_dimensions.length">
            <div class="dim-group-title">
              <span class="group-icon">📝</span> 文本评测
            </div>
            <div class="dimension-list">
              <div
                v-for="dim in scoreReport.text_dimensions"
                :key="dim.label"
                class="dimension-item"
              >
                <div class="dim-header">
                  <span class="dim-label">{{ dim.label }}</span>
                  <span class="dim-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span>
                </div>
                <div class="dim-bar-bg">
                  <div
                    class="dim-bar-fill"
                    :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 建议 -->
          <div class="report-suggestions" v-if="scoreReport.suggestions">
            <div class="suggestion-icon">💬</div>
            <p>{{ scoreReport.suggestions }}</p>
          </div>
        </div>

        <div class="report-loading" v-else>
          <div class="loading-spinner"></div>
          <p>正在生成报告...</p>
        </div>

        <div class="report-actions">
          <button class="retry-btn" @click="selectScenario(selectedScenario)">
            <span>🔄</span> 再来一次
          </button>
          <button class="back-btn" @click="backToScenes">
            <span>🏠</span> 返回场景
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.voice-call-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 60%, #F0F8FF 100%);
  color: #4A4A5A;
  font-family: 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}

// ========== 场景选择 ==========
.call-select-header {
  text-align: center;
  padding: 48px 20px 0;

  .header-mascot {
    font-size: 56px;
    animation: bounce 2s ease-in-out infinite;
    display: inline-block;
  }
  h2 {
    font-size: 26px;
    font-weight: 700;
    margin: 12px 0 8px;
    color: #3D3D5C;
  }
  .select-subtitle {
    color: #999;
    font-size: 15px;
  }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.call-scenario-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding: 28px 20px;
  max-width: 440px;
  margin: 0 auto;
}

.call-scenario-card {
  background: #fff;
  border: 2px solid #F0E8FF;
  border-radius: 20px;
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  &:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  }

  .csc-emoji {
    font-size: 40px;
    margin-bottom: 10px;
  }
  h4 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 4px;
    color: #3D3D5C;
  }
  p {
    font-size: 12px;
    color: #aaa;
  }
}

.select-footer {
  text-align: center;
  padding-bottom: 40px;
  .back-btn {
    color: #999;
    font-size: 14px;
  }
}

// ========== 通话界面 ==========
.call-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 100vh;
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 25%, #FFF9F0 50%, #F0F8FF 100%);
}

.call-top {
  text-align: center;
  padding: 40px 20px 0;
}

.call-scene-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #7C6FF7;
  background: rgba(124, 111, 247, 0.08);
  padding: 8px 18px;
  border-radius: 24px;
  .pill-emoji {
    font-size: 16px;
  }
}

.call-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
}

// 可爱头像 + 波纹
.mascot-container {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;

  .ripple-ring {
    position: absolute;
    border-radius: 50%;
    border: 2.5px solid rgba(255, 107, 138, 0.15);
    animation: none;
  }
  .r1 { width: 100%; height: 100%; }
  .r2 { width: 78%; height: 78%; }
  .r3 { width: 56%; height: 56%; }

  &.ai_speaking .ripple-ring {
    border-color: rgba(255, 107, 138, 0.25);
    animation: ripple 1.6s ease-out infinite;
  }
  &.ai_speaking .r2 { animation-delay: 0.35s; }
  &.ai_speaking .r3 { animation-delay: 0.7s; }

  &.listening .ripple-ring {
    border-color: rgba(91, 143, 249, 0.3);
    animation: ripple 1.3s ease-out infinite;
  }
  &.listening .r2 { animation-delay: 0.25s; }
  &.listening .r3 { animation-delay: 0.5s; }

  &.thinking .ripple-ring {
    border-color: rgba(246, 189, 22, 0.3);
    animation: ripple 0.9s ease-out infinite;
  }
  &.thinking .r2 { animation-delay: 0.2s; }
  &.thinking .r3 { animation-delay: 0.4s; }

  .mascot-avatar {
    width: 74px;
    height: 74px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FFE0E8, #FFD6E0);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    box-shadow: 0 4px 16px rgba(255, 107, 138, 0.15);

    .mascot-face {
      font-size: 38px;
      animation: wiggle 3s ease-in-out infinite;
    }
  }
}

@keyframes ripple {
  0% { transform: scale(0.8); opacity: 0.5; }
  100% { transform: scale(1.7); opacity: 0; }
}

@keyframes wiggle {
  0%, 100% { transform: rotate(0); }
  25% { transform: rotate(5deg); }
  75% { transform: rotate(-5deg); }
}

.call-state-label {
  font-size: 16px;
  color: #999;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;

  .state-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;

    &.speaking {
      background: #FF6B8A;
      animation: pulse-dot 0.8s ease-in-out infinite;
    }
    &.listening {
      background: #5B8FF9;
      animation: pulse-dot 0.8s ease-in-out infinite;
    }
    &.thinking {
      background: #F6BD16;
      animation: pulse-dot 0.5s ease-in-out infinite;
    }
  }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

// 字幕
.call-subtitles {
  padding: 0 24px 20px;
  max-width: 520px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.subtitle {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 85%;

  .subtitle-avatar {
    font-size: 22px;
    flex-shrink: 0;
    line-height: 1;
  }
  .subtitle-text {
    color: #4A4A5A;
  }
}

.user-subtitle {
  background: #fff;
  box-shadow: 0 2px 8px rgba(91, 143, 249, 0.1);
  align-self: flex-end;
  border-bottom-right-radius: 6px;
}

.ai-subtitle {
  background: #fff;
  box-shadow: 0 2px 8px rgba(255, 107, 138, 0.1);
  align-self: flex-start;
  border-bottom-left-radius: 6px;
}

// 挂断
.call-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 44px;
}

.hangup-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #FF6B8A, #FF8E9E);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(255, 107, 138, 0.3);
  transition: all 0.25s;

  .hangup-icon {
    font-size: 24px;
  }

  &:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 24px rgba(255, 107, 138, 0.4);
  }
  &:active {
    transform: scale(0.95);
  }
}

.hangup-label {
  font-size: 12px;
  color: #bbb;
  margin-top: 8px;
}

// ========== 评分报告 ==========
.report-screen {
  min-height: 100vh;
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 24px;
}

.report-header {
  text-align: center;
  margin-bottom: 24px;

  .report-mascot {
    font-size: 48px;
    margin-bottom: 8px;
  }
  h2 {
    font-size: 24px;
    font-weight: 700;
    color: #3D3D5C;
  }
  .report-scene {
    font-size: 14px;
    color: #999;
    margin-top: 4px;
  }
}

.report-content {
  width: 100%;
  max-width: 380px;
}

// 综合分圆圈
.overall-circle {
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto 28px;

  .overall-num {
    font-size: 42px;
    font-weight: 800;
    color: #3D3D5C;
    line-height: 1;
  }
  .overall-unit {
    font-size: 13px;
    color: #999;
    margin-top: 2px;
  }
  .overall-level {
    font-size: 13px;
    font-weight: 600;
    margin-top: 4px;
    color: #FF6B8A;
  }
}

// 维度分组
.dimension-group {
  margin-bottom: 20px;

  .dim-group-title {
    font-size: 15px;
    font-weight: 600;
    color: #3D3D5C;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;

    .group-icon {
      font-size: 18px;
    }
  }
}

// 维度列表
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

.dimension-item {
  .dim-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    .dim-label {
      font-size: 14px;
      color: #666;
    }
    .dim-score {
      font-size: 14px;
      font-weight: 700;
    }
  }
  .dim-bar-bg {
    height: 8px;
    border-radius: 4px;
    background: #F0E8FF;
    overflow: hidden;
  }
  .dim-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
  }
}

// 建议
.report-suggestions {
  display: flex;
  gap: 10px;
  padding: 16px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  .suggestion-icon {
    font-size: 22px;
    flex-shrink: 0;
  }
  p {
    font-size: 14px;
    color: #666;
    line-height: 1.6;
  }
}

// 加载
.report-loading {
  text-align: center;
  padding: 40px;
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #F0E8FF;
    border-top-color: #FF6B8A;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 16px;
  }
  p {
    color: #999;
    font-size: 14px;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 报告按钮
.report-actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;

  .retry-btn, .back-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 12px 24px;
    border-radius: 24px;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;

    span { font-size: 16px; }
  }
  .retry-btn {
    background: linear-gradient(135deg, #FF6B8A, #FF8E9E);
    color: #fff;
    box-shadow: 0 4px 12px rgba(255, 107, 138, 0.3);
    &:hover { transform: translateY(-2px); }
  }
  .back-btn {
    background: #fff;
    color: #666;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    &:hover { transform: translateY(-2px); }
  }
}
</style>