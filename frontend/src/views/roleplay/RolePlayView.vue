<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import { streamStartRoleplay, streamSpeakRoleplay, ttsRoleplay, endRoleplay } from '@/api/roleplay'
import DimensionBars from '@/components/common/DimensionBars.vue'

const router = useRouter()

// ========== 角色配置 ==========
const ROLES = [
  { id: 'interviewee', title: '面试者', aiRole: '面试官', desc: '英文工作面试模拟',
    emoji: '💼', color: '#A78BFA',
    topics: '自我介绍/项目经历/职业规划/优缺点' },
  { id: 'waiter', title: '服务员', aiRole: '顾客', desc: '餐厅服务场景',
    emoji: '🍽️', color: '#86EFAC',
    topics: '迎宾/推荐菜品/处理忌口/结账' },
  { id: 'guide', title: '导游', aiRole: '游客', desc: '景点导览场景',
    emoji: '🗺️', color: '#93C5FD',
    topics: '景点介绍/交通指引/餐饮推荐' },
]

// ========== 状态 ==========
const phase = ref('select') // select | calling | report
const selectedRole = ref(null)
const sessionId = ref('')
const callState = ref('idle') // idle | ai_speaking | listening | thinking
const subtitle = ref('')
const userSubtitle = ref('')
const isConnecting = ref(false)
const scoreReport = ref(null)
const isScoring = ref(false)

// 消息列表（用于显示对话记录）
const messages = ref([])

// 音频相关
let currentAudio = null

// ========== 角色选择 ==========
async function selectRole(role) {
  selectedRole.value = role
  phase.value = 'calling'
  callState.value = 'idle'
  subtitle.value = ''
  userSubtitle.value = ''
  messages.value = []

  isConnecting.value = true
  streamStartRoleplay(role.id, 'B1', {
    onToken(text) {
      subtitle.value += text
    },
    onDone(data) {
      isConnecting.value = false
      sessionId.value = data.session_id
      subtitle.value = data.full_text
      messages.value.push({ role: 'ai', text: data.full_text })
      speakAndListen(data.full_text)
    },
    onError() {
      isConnecting.value = false
      subtitle.value = 'Connection failed. Please try again.'
    },
  })
}

// ========== AI 说话 + 自动听 ==========
async function speakAndListen(text) {
  callState.value = 'ai_speaking'
  try {
    const ttsData = await ttsRoleplay(text)
    const blob = base64ToBlob(ttsData.audio_base64, 'audio/mpeg')
    const url = URL.createObjectURL(blob)
    currentAudio = new Audio(url)
    currentAudio.onended = () => {
      URL.revokeObjectURL(url)
      startListening()
    }
    currentAudio.onerror = () => {
      startListening()
    }
    await currentAudio.play()
  } catch (e) {
    startListening()
  }
}

// ========== 录音 ==========
let mediaRecorder = null
let audioChunks = []
let stream = null
let silenceTimer = null
let audioContext = null
let analyser = null
const SILENCE_THRESHOLD = 0.02
const SILENCE_DURATION = 1500

async function startListening() {
  callState.value = 'listening'
  userSubtitle.value = ''
  audioChunks = []

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: 16000, channelCount: 1 }
    })
  } catch (e) {
    callState.value = 'idle'
    return
  }

  mediaRecorder = new MediaRecorder(stream)
  audioChunks = []

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data)
  }

  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach(t => t.stop())
    clearTimeout(silenceTimer)
    const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' })
    await handleUserSpeech(blob)
  }

  mediaRecorder.start()

  // 音量检测 + 静音自动停止
  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(stream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    checkSilence()
  } catch (e) {
    // 音量检测失败，等待手动停止
  }
}

function checkSilence() {
  if (callState.value !== 'listening') return
  if (!analyser) return

  const dataArray = new Uint8Array(analyser.frequencyBinCount)
  analyser.getByteTimeDomainData(dataArray)
  let sum = 0
  for (let i = 0; i < dataArray.length; i++) {
    sum += Math.abs(dataArray[i] - 128)
  }
  const avg = sum / dataArray.length / 128

  if (avg < SILENCE_THRESHOLD) {
    if (!silenceTimer) {
      silenceTimer = setTimeout(() => {
        if (mediaRecorder?.state === 'recording') {
          mediaRecorder.stop()
        }
      }, SILENCE_DURATION)
    }
  } else {
    clearTimeout(silenceTimer)
    silenceTimer = null
  }

  requestAnimationFrame(checkSilence)
}

// ========== 处理用户语音 ==========

async function handleUserSpeech(audioBlob) {
  callState.value = 'thinking'
  subtitle.value = ''
  userSubtitle.value = ''

  streamSpeakRoleplay(sessionId.value, selectedRole.value.id, audioBlob, {
    onAsr(text) {
      userSubtitle.value = text
      messages.value.push({ role: 'user', text })
    },
    onToken(text) {
      subtitle.value += text
    },
    onDone(data) {
      const fullText = data.full_text
      subtitle.value = fullText
      messages.value.push({ role: 'ai', text: fullText })

      if (data.conversation_complete) {
        setTimeout(() => endRoleplaySession(), 500)
      } else {
        speakAndListen(fullText)
      }
    },
    onError() {
      callState.value = 'idle'
    },
  })
}

// ========== 结束对话 ==========
async function endRoleplaySession() {
  if (isScoring.value) return
  isScoring.value = true
  callState.value = 'idle'
  subtitle.value = '正在评测中...'

  try {
    const result = await endRoleplay(sessionId.value)
    scoreReport.value = {
      overall: result.overall,
      dimensions: result.dimensions || [],
      suggestions: result.suggestions || '',
      utterances: result.utterances || [],
      transcript: result.transcript || [],
      pronunciation: result.pronunciation || [],
      dimension_details: result.dimension_details || [],
      scoring_methodology: result.scoring_methodology || '',
    }
    phase.value = 'report'
  } catch (e) {
    subtitle.value = '评测失败，请重试'
  } finally {
    isScoring.value = false
  }
}

function manualEnd() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
  stream?.getTracks().forEach(t => t.stop())
  endRoleplaySession()
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

// ========== 评分维度颜色 ==========
function dimBarColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

// ========== 清理 ==========
onUnmounted(() => {
  if (currentAudio) { currentAudio.pause(); currentAudio = null }
  if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
  stream?.getTracks().forEach(t => t.stop())
})
</script>

<template>
  <div class="roleplay-page">
    <!-- ========== 阶段1: 角色选择 ========== -->
    <template v-if="phase === 'select'">
      <div class="rp-select-header">
        <div class="header-mascot">🎭</div>
        <h2>情景角色扮演</h2>
        <p class="select-subtitle">选择一个角色，AI 扮演对方与你进行真实语音对话</p>
      </div>

      <div class="role-grid">
        <div
          v-for="role in ROLES"
          :key="role.id"
          class="role-card"
          :style="{ '--role-color': role.color }"
          @click="selectRole(role)"
        >
          <div class="role-emoji">{{ role.emoji }}</div>
          <h3>{{ role.title }}</h3>
          <div class="role-ai">AI 扮演：{{ role.aiRole }}</div>
          <p class="role-desc">{{ role.desc }}</p>
          <div class="role-tags">
            <span v-for="topic in role.topics.split('/')" :key="topic" class="tag">{{ topic }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 阶段2: 通话界面 ========== -->
    <template v-if="phase === 'calling'">
      <div class="call-screen">
        <!-- 顶部：角色信息 + 退出 -->
        <div class="call-top">
          <button class="back-btn" @click="manualEnd">
            <el-icon><ArrowLeft /></el-icon>
            <span>结束</span>
          </button>
          <div class="call-role-pill">
            <span>{{ selectedRole.emoji }}</span>
            <span>{{ selectedRole.title }} ← → {{ selectedRole.aiRole }}</span>
          </div>
        </div>

        <!-- 中间：头像 + 状态 -->
        <div class="call-center">
          <div v-if="isConnecting" class="connecting-hint">正在连接 AI 角色...</div>

          <div v-if="!isConnecting" class="mascot-container">
            <div class="mascot-ring" :class="callState"></div>
            <div class="mascot-avatar">{{ selectedRole.emoji }}</div>
          </div>

          <!-- AI 字幕 -->
          <div v-if="subtitle && !isConnecting" class="subtitle-box ai">
            <div class="subtitle-label">{{ selectedRole.aiRole }}</div>
            <div class="subtitle-text">{{ subtitle }}</div>
          </div>

          <!-- 用户字幕 -->
          <div v-if="userSubtitle" class="subtitle-box user">
            <div class="subtitle-label">{{ selectedRole.title }}（你）</div>
            <div class="subtitle-text">{{ userSubtitle }}</div>
          </div>

          <!-- 状态文字 -->
          <div v-if="!isConnecting" class="call-status">
            <template v-if="callState === 'ai_speaking'">AI 角色正在说话...</template>
            <template v-else-if="callState === 'listening'">正在听你说话...</template>
            <template v-else-if="callState === 'thinking'">AI 角色思考中...</template>
            <template v-else-if="callState === 'idle'">点击下方按钮对话</template>
          </div>
        </div>

        <!-- 底部：录音按钮 -->
        <div class="call-bottom">
          <div v-if="!isConnecting" class="record-area">
            <button
              :class="['record-btn', callState]"
              @click="callState === 'listening' ? null : null"
              :disabled="callState !== 'listening'"
            >
              <div v-if="callState === 'listening'" class="recording-indicator">
                <span class="rec-dot"></span>
                <span>录音中...</span>
              </div>
              <el-icon v-else :size="32">
                <Microphone />
              </el-icon>
            </button>
            <p class="record-hint">
              <template v-if="callState === 'listening'">安静1.5秒后自动发送</template>
              <template v-else-if="callState === 'ai_speaking'">请等待 AI 说完</template>
              <template v-else-if="callState === 'thinking'">AI 正在回复中</template>
              <template v-else>准备中...</template>
            </p>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 阶段3: 评分报告 ========== -->
    <template v-if="phase === 'report' && scoreReport">
      <div class="report-screen">
        <!-- 头部 -->
        <div class="report-header">
          <div class="report-mascot">{{ selectedRole.emoji }}</div>
          <h2>{{ selectedRole.title }}角色扮演报告</h2>
          <div class="report-role-info">
            {{ selectedRole.title }} ← → {{ selectedRole.aiRole }}
          </div>
        </div>

        <!-- 综合分 -->
        <div class="report-overall">
          <div class="overall-circle" :style="{ borderColor: dimBarColor(scoreReport.overall) }">
            <span class="overall-num">{{ Math.round(scoreReport.overall) }}</span>
            <span class="overall-label">综合分</span>
          </div>
        </div>

        <!-- 角色维度 -->
        <div class="report-section">
          <h3 class="section-title">角色表现评分</h3>
          <DimensionBars :dimensions="scoreReport.dimensions" />
        </div>

        <!-- 发音维度 -->
        <div v-if="scoreReport.pronunciation && scoreReport.pronunciation.length > 0" class="report-section">
          <h3 class="section-title">发音评测</h3>
          <DimensionBars :dimensions="scoreReport.pronunciation" />
        </div>

        <!-- 综合建议 -->
        <div v-if="scoreReport.suggestions" class="report-section">
          <h3 class="section-title">改进建议</h3>
          <div class="suggestions-text">{{ scoreReport.suggestions }}</div>
        </div>

        <!-- 对话记录 -->
        <div v-if="scoreReport.transcript && scoreReport.transcript.length > 0" class="report-section">
          <h3 class="section-title">对话记录</h3>
          <div class="transcript-list">
            <div v-for="(msg, i) in scoreReport.transcript" :key="i" :class="['transcript-item', msg.role]">
              <span class="transcript-role">{{ msg.role === 'ai' ? selectedRole.aiRole : selectedRole.title }}</span>
              <span class="transcript-text">{{ msg.text }}</span>
            </div>
          </div>
        </div>

        <!-- 按钮 -->
        <div class="report-actions">
          <el-button @click="router.push('/role-play')">返回角色选择</el-button>
          <el-button type="primary" @click="selectRole(selectedRole)">再来一次</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.roleplay-page {
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 60%, #F0F8FF 100%);
  color: #4A4A5A;
  font-family: 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}

/* ========== 角色选择 ========== */
.rp-select-header {
  text-align: center;
  padding: 48px 20px 0;
}
.header-mascot {
  font-size: 56px;
  animation: bounce 2s ease-in-out infinite;
  display: inline-block;
}
.rp-select-header h2 {
  font-size: 26px;
  font-weight: 700;
  margin: 12px 0 8px;
  color: #3D3D5C;
}
.select-subtitle {
  color: #999;
  font-size: 15px;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 960px;
  margin: 32px auto;
  padding: 0 20px;
}

.role-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  border: 1.5px solid var(--color-border);
  border-top: 4px solid var(--role-color);
  border-radius: 16px;
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
}
.role-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.role-emoji {
  font-size: 40px;
  margin-bottom: 8px;
}
.role-card h3 {
  margin: 8px 0 4px;
  font-size: 18px;
  color: #3D3D5C;
}
.role-ai {
  font-size: 13px;
  color: var(--role-color);
  font-weight: 600;
  margin-bottom: 8px;
}
.role-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}
.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}
.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0,0,0,0.04);
  color: #888;
}

/* ========== 通话界面 ========== */
.call-screen {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 25%, #FFF9F0 50%, #F0F8FF 100%);
}

.call-top {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 20px 0;
  position: relative;
}
.back-btn {
  position: absolute;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: rgba(0,0,0,0.04);
  padding: 6px 12px;
  border-radius: 20px;
  cursor: pointer;
  color: #666;
  font-size: 13px;
  transition: background 0.2s;
}
.back-btn:hover { background: rgba(0,0,0,0.08); }

.call-role-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #7C6FF7;
  background: rgba(124,111,247,0.08);
  padding: 8px 18px;
  border-radius: 24px;
}

.call-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px;
}

.connecting-hint {
  font-size: 16px;
  color: #999;
  animation: pulse-text 1.5s ease-in-out infinite;
}
@keyframes pulse-text {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.mascot-container {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mascot-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid transparent;
  transition: all 0.3s;
}
.mascot-ring.ai_speaking {
  border-color: #7C6FF7;
  box-shadow: 0 0 20px rgba(124,111,247,0.3);
  animation: ring-pulse 1.5s ease-in-out infinite;
}
.mascot-ring.listening {
  border-color: #5AD8A6;
  box-shadow: 0 0 20px rgba(90,216,166,0.3);
  animation: ring-pulse 0.8s ease-in-out infinite;
}
.mascot-ring.thinking {
  border-color: #F6BD16;
  box-shadow: 0 0 20px rgba(246,189,22,0.3);
  animation: ring-pulse 1s ease-in-out infinite;
}
@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.08); opacity: 1; }
}
.mascot-avatar {
  font-size: 60px;
  z-index: 1;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}

.subtitle-box {
  max-width: 520px;
  width: 100%;
  text-align: center;
}
.subtitle-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
}
.subtitle-box.ai .subtitle-label { color: #7C6FF7; }
.subtitle-box.user .subtitle-label { color: #5AD8A6; }
.subtitle-text {
  font-size: 18px;
  line-height: 1.5;
  color: #3D3D5C;
  font-weight: 500;
}

.call-status {
  font-size: 14px;
  color: #999;
}

.call-bottom {
  padding: 20px;
  display: flex;
  justify-content: center;
}
.record-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.record-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}
.record-btn.listening {
  background: #5AD8A6;
  color: #fff;
  box-shadow: 0 4px 16px rgba(90,216,166,0.4);
  animation: pulse-record 1s ease-in-out infinite;
}
@keyframes pulse-record {
  0%, 100% { box-shadow: 0 0 0 0 rgba(90,216,166,0.4); }
  50% { box-shadow: 0 0 0 16px rgba(90,216,166,0); }
}
.record-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.recording-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}
.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  animation: blink 0.5s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.record-hint {
  font-size: 13px;
  color: #999;
}

/* ========== 评分报告 ========== */
.report-screen {
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 100%);
  padding: 24px 24px 32px;
  max-width: 800px;
  margin: 0 auto;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
}
.report-mascot { font-size: 40px; margin-bottom: 4px; }
.report-header h2 { font-size: 22px; font-weight: 700; color: #3D3D5C; margin: 0; }
.report-role-info { font-size: 13px; color: #999; margin-top: 4px; }

.report-overall {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.overall-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 6px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.8);
}
.overall-num { font-size: 38px; font-weight: 800; color: #3D3D5C; line-height: 1; }
.overall-label { font-size: 12px; color: #999; margin-top: 2px; }

.report-section {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #3D3D5C;
  margin: 0 0 14px;
}

.suggestions-text {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  white-space: pre-wrap;
}

.transcript-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}
.transcript-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(0,0,0,0.02);
}
.transcript-role {
  flex-shrink: 0;
  font-weight: 600;
  color: #7C6FF7;
  min-width: 50px;
}
.transcript-item.user .transcript-role { color: #5AD8A6; }
.transcript-text { color: #555; line-height: 1.5; }

.report-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .role-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
  }
}
</style>