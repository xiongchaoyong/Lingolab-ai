<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { streamStartRoleplay, streamSpeakRoleplay, ttsRoleplay, endRoleplay } from '@/api/roleplay'
import UtteranceDetailPanel from '@/components/pronunciation/UtteranceDetailPanel.vue'

const router = useRouter()

// ========== 角色配置 ==========
const ROLES = [
  { id: 'interviewee', title: '面试者', subtitle: 'AI 扮演面试官，模拟英文工作面试', emoji: '💼', color: '#A78BFA' },
  { id: 'waiter', title: '服务员', subtitle: 'AI 扮演顾客，练习餐厅服务场景', emoji: '🍽️', color: '#5AD8A6' },
  { id: 'guide', title: '导游', subtitle: 'AI 扮演游客，练习景点导览场景', emoji: '🗺️', color: '#5B8FF9' },
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

// 报告数据计算属性
const hasDetailedReport = computed(() => {
  return scoreReport.value?.utterances?.length > 0
})

const aggregatedErrors = computed(() => {
  if (!scoreReport.value?.utterances) return []
  const errorMap = new Map()
  for (const utt of scoreReport.value.utterances) {
    for (const err of utt.errors || []) {
      const key = err.phoneme
      if (!errorMap.has(key) || errorMap.get(key).score > err.score) {
        errorMap.set(key, err)
      }
    }
  }
  return [...errorMap.values()].sort((a, b) => a.score - b.score)
})

const expandedUtterance = ref(null)
function toggleUtterance(index) {
  expandedUtterance.value = expandedUtterance.value === index ? null : index
}

// 音频相关
let audioContext = null
let analyser = null
let mediaRecorder = null
let audioChunks = []
let silenceTimer = null
let currentAudio = null
const SILENCE_THRESHOLD = 0.02
const SILENCE_DURATION = 1500

// ========== 角色选择 ==========
async function selectRole(role) {
  selectedRole.value = role
  phase.value = 'calling'
  callState.value = 'idle'
  subtitle.value = ''
  userSubtitle.value = ''

  // 开始角色扮演
  isConnecting.value = true
  streamStartRoleplay(role.id, 'B1', {
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
    const ttsData = await ttsRoleplay(text)
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

  streamSpeakRoleplay(sessionId.value, selectedRole.value.id, audioBlob, {
    onAsr(text) {
      userSubtitle.value = text
    },
    onToken(text) {
      subtitle.value += text
    },
    onDone(data) {
      subtitle.value = data.full_text
      if (data.conversation_complete) {
        // 对话达到最大轮次，自动结束评分
        setTimeout(() => hangUp(), 500)
      } else {
        // AI 回复 → 播放语音
        speakAndListen(data.full_text)
      }
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
    phase.value = 'report'
    try {
      scoreReport.value = await endRoleplay(sessionId.value)
    } catch (e) {
      scoreReport.value = {
        overall: 0,
        pronunciation: [],
        dimensions: [],
        dimension_details: [],
        suggestions: '评分服务暂时异常，请稍后重试',
        utterances: [],
        transcript: [],
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
  selectedRole.value = null
  callState.value = 'idle'
  subtitle.value = ''
  userSubtitle.value = ''
  scoreReport.value = null
  sessionId.value = ''
}

function backToRoles() {
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
  <div class="roleplay-page">
    <!-- 角色选择 -->
    <template v-if="phase === 'select'">
      <div class="rp-select-header">
        <div class="header-mascot">🎭</div>
        <h2>情景角色扮演</h2>
        <p class="select-subtitle">选一个角色，和 AI 进行真实语音对话吧~</p>
      </div>
      <div class="rp-role-grid">
        <div
          v-for="role in ROLES"
          :key="role.id"
          class="rp-role-card"
          :style="{ '--accent': role.color }"
          @click="selectRole(role)"
        >
          <div class="rrc-emoji">{{ role.emoji }}</div>
          <h4>{{ role.title }}</h4>
          <p>{{ role.subtitle }}</p>
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
        <!-- 顶部角色标签 -->
        <div class="call-top">
          <div class="call-role-pill">
            <span class="pill-emoji">{{ selectedRole?.emoji }}</span>
            {{ selectedRole?.title }}
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
              <span class="mascot-face">{{ selectedRole?.emoji }}</span>
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
            <span class="subtitle-avatar">{{ selectedRole?.emoji }}</span>
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
        <!-- 加载中 -->
        <template v-if="isScoring || !scoreReport">
          <div class="report-header">
            <div class="report-mascot">🌟</div>
            <h2>角色扮演报告</h2>
          </div>
          <div class="report-loading">
            <div class="loading-spinner"></div>
            <p>正在生成报告...</p>
          </div>
        </template>

        <!-- 报告内容 -->
        <template v-else>
          <!-- 顶部：标题 + 综合分 + 方法论 -->
          <div class="report-top">
            <div class="report-header">
              <div class="report-mascot">🌟</div>
              <h2>角色扮演报告</h2>
              <p class="report-role">{{ selectedRole?.emoji }} {{ selectedRole?.title }} 角色</p>
            </div>

            <div class="overall-area">
              <div class="overall-circle" :style="{ '--score': scoreReport.overall }">
                <span class="overall-num">{{ scoreReport.overall }}</span>
                <span class="overall-unit">分</span>
                <span class="overall-level">
                  {{ scoreReport.overall >= 80 ? '🎉 优秀' : scoreReport.overall >= 60 ? '👍 良好' : '💪 加油' }}
                </span>
              </div>
              <div class="methodology-card" v-if="scoreReport.scoring_methodology">
                <div class="methodology-title">📐 评分计算方式</div>
                <pre class="methodology-text">{{ scoreReport.scoring_methodology }}</pre>
              </div>
            </div>
          </div>

          <!-- 主体：双列网格 -->
          <div class="report-main">
            <!-- 左列：语音评测 -->
            <section class="report-card" v-if="scoreReport.pronunciation?.length">
              <div class="card-title">
                <span class="card-icon">🎤</span> 语音评测
              </div>
              <div class="dimension-list">
                <div v-for="dim in scoreReport.pronunciation" :key="dim.label" class="dimension-item">
                  <div class="dim-header">
                    <span class="dim-label">{{ dim.label }}</span>
                    <span class="dim-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span>
                  </div>
                  <div class="dim-bar-bg">
                    <div class="dim-bar-fill" :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"></div>
                  </div>
                </div>
              </div>

              <div class="error-section" v-if="aggregatedErrors.length > 0">
                <div class="error-title">⚠️ 问题音素</div>
                <div v-for="err in aggregatedErrors" :key="err.phoneme" class="error-item">
                  <el-tag type="danger" size="small">{{ err.phoneme }}</el-tag>
                  <span class="error-actual">{{ err.actual }}</span>
                  <span class="error-tip-text">{{ err.tip }}</span>
                </div>
              </div>
            </section>

            <!-- 右列：角色表现评测 -->
            <section class="report-card" v-if="scoreReport.dimension_details?.length">
              <div class="card-title">
                <span class="card-icon">🎭</span> 角色表现评测（LLM）
              </div>
              <div class="text-dim-cards">
                <div v-for="dim in scoreReport.dimension_details" :key="dim.label" class="text-dim-card">
                  <div class="tdc-header">
                    <span class="tdc-label">{{ dim.label }}</span>
                    <span class="tdc-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span>
                  </div>
                  <div class="dim-bar-bg" style="margin-bottom: 8px;">
                    <div class="dim-bar-fill" :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"></div>
                  </div>
                  <div class="tdc-feedback" v-if="dim.feedback">{{ dim.feedback }}</div>
                  <div class="tdc-tags">
                    <span v-if="dim.strengths" class="tdc-tag good">✅ {{ dim.strengths }}</span>
                    <span v-if="dim.weaknesses" class="tdc-tag improve">📌 {{ dim.weaknesses }}</span>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <!-- 逐句发音分析（全宽） -->
          <section class="report-card report-card--full" v-if="hasDetailedReport">
            <div class="card-title">
              <span class="card-icon">📋</span> 逐句发音分析
            </div>
            <div class="utterance-grid">
              <div
                v-for="(utt, idx) in scoreReport.utterances"
                :key="idx"
                class="utterance-item"
                :class="{ expanded: expandedUtterance === idx }"
              >
                <div class="utterance-header" @click="toggleUtterance(idx)">
                  <span class="utterance-num">#{{ idx + 1 }}</span>
                  <span class="utterance-text-preview">{{ utt.text?.slice(0, 60) }}{{ utt.text?.length > 60 ? '...' : '' }}</span>
                  <span class="utterance-score" :style="{ color: dimScoreColor(utt.overall) }">{{ utt.overall }}</span>
                  <span class="utterance-arrow" :class="{ expanded: expandedUtterance === idx }">▶</span>
                </div>
                <div class="utterance-detail-wrap" v-show="expandedUtterance === idx">
                  <UtteranceDetailPanel :pronunciation-data="utt" :text="utt.text" />
                </div>
              </div>
            </div>
          </section>

          <!-- 底部双列：对话记录 + 建议 -->
          <div class="report-bottom">
            <section class="report-card" v-if="scoreReport.transcript?.length">
              <div class="card-title">
                <span class="card-icon">💬</span> 对话记录
              </div>
              <div class="transcript-list">
                <div v-for="(msg, idx) in scoreReport.transcript" :key="idx" class="transcript-msg" :class="msg.role">
                  <div class="transcript-role">{{ msg.role === 'user' ? '😊 你' : selectedRole?.emoji + ' AI' }}</div>
                  <div class="transcript-bubble">{{ msg.text }}</div>
                </div>
              </div>
            </section>

            <section class="report-card" v-if="scoreReport.suggestions">
              <div class="card-title">
                <span class="card-icon">💡</span> 改进建议
              </div>
              <div class="suggestions-content">
                <p>{{ scoreReport.suggestions }}</p>
              </div>
            </section>
          </div>

          <!-- 操作按钮 -->
          <div class="report-actions">
            <button class="retry-btn" @click="selectRole(selectedRole)">
              <span>🔄</span> 再来一次
            </button>
            <button class="back-btn" @click="backToRoles">
              <span>🏠</span> 返回角色选择
            </button>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.roleplay-page {
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 60%, #F0F8FF 100%);
  color: #4A4A5A;
  font-family: 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}

// ========== 角色选择 ==========
.rp-select-header {
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

.rp-role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding: 28px 20px;
  max-width: 440px;
  margin: 0 auto;
}

.rp-role-card {
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

  .rrc-emoji {
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
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 25%, #FFF9F0 50%, #F0F8FF 100%);
}

.call-top {
  text-align: center;
  padding: 40px 20px 0;
}

.call-role-pill {
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
  min-height: calc(100vh - 56px);
  background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 100%);
  padding: 24px 24px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.report-header {
  text-align: center;
  margin-bottom: 16px;
  .report-mascot { font-size: 40px; margin-bottom: 4px; }
  h2 { font-size: 22px; font-weight: 700; color: #3D3D5C; margin: 0; }
  .report-role { font-size: 13px; color: #999; margin-top: 4px; }
}

// 顶部：综合分 + 方法论
.report-top {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding: 20px 28px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
}

.overall-area {
  display: flex;
  align-items: center;
  gap: 28px;
  flex: 1;
}

.overall-circle {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  .overall-num { font-size: 38px; font-weight: 800; color: #3D3D5C; line-height: 1; }
  .overall-unit { font-size: 12px; color: #999; margin-top: 2px; }
  .overall-level { font-size: 12px; font-weight: 600; margin-top: 2px; color: #FF6B8A; }
}

.methodology-card {
  flex: 1;
  padding: 14px 18px;
  background: #F8F0FF;
  border-radius: 14px;
  .methodology-title { font-size: 13px; font-weight: 600; color: #7C6FF7; margin-bottom: 6px; }
  .methodology-text {
    font-size: 12px; color: #666; line-height: 1.7;
    white-space: pre-wrap; font-family: inherit; margin: 0;
  }
}

// 主体双列
.report-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

// 底部双列
.report-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

// 通用卡片
.report-card {
  background: #fff;
  border-radius: 20px;
  padding: 20px 28px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  &--full {
    grid-column: 1 / -1;
    margin-bottom: 16px;
  }
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #3D3D5C;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  .card-icon { font-size: 18px; }
}

// 维度列表
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dimension-item {
  .dim-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
    .dim-label { font-size: 13px; color: #666; }
    .dim-score { font-size: 14px; font-weight: 700; }
  }
  .dim-bar-bg {
    height: 7px;
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

// 错误音素
.error-section {
  margin-top: 16px;
  .error-title { font-size: 13px; font-weight: 600; color: #3D3D5C; margin-bottom: 8px; }
}

.error-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(255, 107, 138, 0.04);
  border-radius: 8px;
  margin-bottom: 6px;
  .error-actual { font-size: 12px; color: #FF6B8A; font-family: monospace; }
  .error-tip-text { font-size: 11px; color: #999; flex: 1; }
}

// 文本维度卡片
.text-dim-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.text-dim-card {
  padding: 14px;
  background: #FAFAFF;
  border-radius: 14px;
  border: 1px solid #F0E8FF;
  .tdc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .tdc-label { font-size: 14px; font-weight: 600; color: #3D3D5C; }
  .tdc-score { font-size: 22px; font-weight: 800; }
  .tdc-feedback { font-size: 12px; color: #666; line-height: 1.5; margin-bottom: 6px; }
  .tdc-tags { display: flex; flex-direction: column; gap: 3px; }
  .tdc-tag { font-size: 11px; &.good { color: #5AD8A6; } &.improve { color: #FF6B8A; } }
}

// 逐句网格
.utterance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 10px;
}

.utterance-item {
  border: 1px solid #F0E8FF;
  border-radius: 12px;
  overflow: hidden;
  &.expanded { grid-column: 1 / -1; }
}

.utterance-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.2s;
  &:hover { background: #FAFAFF; }
  .utterance-num {
    font-size: 11px; font-weight: 600; color: #7C6FF7;
    background: rgba(124, 111, 247, 0.08);
    padding: 2px 8px; border-radius: 8px; flex-shrink: 0;
  }
  .utterance-text-preview {
    font-size: 13px; color: #666;
    flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .utterance-score { font-size: 15px; font-weight: 700; flex-shrink: 0; }
  .utterance-arrow {
    font-size: 10px; color: #ccc; flex-shrink: 0;
    transition: transform 0.25s;
    &.expanded { transform: rotate(90deg); }
  }
}

.utterance-detail-wrap {
  border-top: 1px solid #F0E8FF;
  padding: 0 16px 8px;
}

// 对话记录
.transcript-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.transcript-msg {
  display: flex;
  flex-direction: column;
  max-width: 90%;
  &.user { align-self: flex-end; }
  &.ai { align-self: flex-start; }
  .transcript-role { font-size: 10px; color: #999; margin-bottom: 2px; padding: 0 4px; }
  &.user .transcript-role { text-align: right; }
  .transcript-bubble {
    padding: 8px 12px; border-radius: 12px; font-size: 12px; line-height: 1.5; color: #4A4A5A;
  }
  &.user .transcript-bubble { background: #F0F0FF; border-bottom-right-radius: 4px; }
  &.ai .transcript-bubble { background: #FFF0F3; border-bottom-left-radius: 4px; }
}

// 建议
.suggestions-content {
  p { font-size: 13px; color: #666; line-height: 1.7; margin: 0; }
}

// 加载
.report-loading {
  text-align: center;
  padding: 80px 20px;
  .loading-spinner {
    width: 40px; height: 40px;
    border: 3px solid #F0E8FF;
    border-top-color: #FF6B8A;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 16px;
  }
  p { color: #999; font-size: 14px; }
}

@keyframes spin { to { transform: rotate(360deg); } }

// 按钮
.report-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 8px;
  .retry-btn, .back-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 10px 22px; border-radius: 22px; border: none;
    font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s;
    span { font-size: 16px; }
  }
  .retry-btn {
    background: linear-gradient(135deg, #FF6B8A, #FF8E9E);
    color: #fff; box-shadow: 0 4px 12px rgba(255, 107, 138, 0.3);
    &:hover { transform: translateY(-2px); }
  }
  .back-btn {
    background: #fff; color: #666;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    &:hover { transform: translateY(-2px); }
  }
}
</style>