<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import { streamStartConversation, streamSpeakConversation, ttsStreamUrl, ttsCachedUrl, endConversation } from '@/api/conversation'
import UtteranceDetailPanel from '@/components/pronunciation/UtteranceDetailPanel.vue'

const router = useRouter()
const authStore = useAuthStore()

// ========== 场景配置 ==========
const SCENARIOS = [
  { id: 'self_intro', title: '自我介绍', subtitle: '聊聊你自己吧', emoji: '👋', color: '#FF6B8A' },
  { id: 'directions', title: '问路指路', subtitle: '帮助迷路的朋友', emoji: '🗺️', color: '#5B8FF9' },
  { id: 'shopping', title: '购物', subtitle: '一起逛街购物', emoji: '🛍️', color: '#F6BD16' },
  { id: 'restaurant', title: '餐厅', subtitle: '享受美食时光', emoji: '🍽️', color: '#5AD8A6' },
  { id: 'hotel', title: '酒店入住', subtitle: '办理入住与咨询', emoji: '🏨', color: '#F5A623' },
  { id: 'airport', title: '机场出行', subtitle: '值机登机与问询', emoji: '✈️', color: '#4A90D9' },
  { id: 'hospital', title: '医院就诊', subtitle: '看病就医场景', emoji: '🏥', color: '#E74C3C' },
  { id: 'school', title: '校园生活', subtitle: '学校日常交流', emoji: '🏫', color: '#2ECC71' },
]

// ========== 状态 ==========
const phase = ref('select') // select | calling | report
const selectedScenario = ref(null)
const sessionId = ref('')
const callState = ref('idle') // idle | ai_speaking | listening | thinking | paused
const isConnecting = ref(false)
const isPaused = ref(false)
const scoreReport = ref(null)
const isScoring = ref(false)

// 对话记录（滚动展示）
const messages = ref([])  // [{role: 'user'|'ai', text, grammar?, streaming?}]
const chatBoxRef = ref(null)
let currentUserMsgIdx = -1  // 当前等待语法纠错的用户消息索引

// 语法错误类型颜色映射
const ERROR_TYPE_COLORS = {
  tense: '#E6A23C',
  subject_verb_agreement: '#F56C6C',
  article: '#909399',
  preposition: '#67C23A',
  word_order: '#409EFF',
  plural: '#E6A23C',
  word_choice: '#9B59B6',
  other: '#909399',
}

const ERROR_TYPE_LABELS = {
  tense: '时态',
  subject_verb_agreement: '主谓一致',
  article: '冠词',
  preposition: '介词',
  word_order: '语序',
  plural: '复数',
  word_choice: '用词',
  other: '其他',
}

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

// 滚动到底部
async function scrollToBottom() {
  await nextTick()
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  }
}

// 逐字流式显示用户文本
function typewriteUserText(idx, fullText) {
  let pos = 0
  const speed = 15  // 每字间隔 ms，模拟流式速度
  function step() {
    if (isHangingUp) return
    if (pos < fullText.length && idx < messages.value.length) {
      messages.value[idx].text = fullText.slice(0, ++pos)
      scrollToBottom()
      setTimeout(step, speed * (Math.random() * 0.5 + 0.75))  // 模拟 token 随机性
    }
  }
  step()
}

// 音频相关
let audioContext = null
let analyser = null
let mediaRecorder = null
let audioChunks = []
let silenceTimer = null
let currentAudio = null
let vadRaF = null  // VAD requestAnimationFrame ID
let isHangingUp = false  // 挂断中，阻止后续操作
const SILENCE_THRESHOLD = 0.02  // 音量阈值
const SILENCE_DURATION = 2500   // 静音 2.5 秒后自动停止

// ========== 场景选择 ==========
async function selectScenario(scenario) {
  selectedScenario.value = scenario
  phase.value = 'calling'
  callState.value = 'idle'
  isPaused.value = false
  messages.value = []
  currentUserMsgIdx = -1

  // 开始对话
  isConnecting.value = true
  streamStartConversation(scenario.id, 'B1', {
    onToken(text) {
      if (isConnecting.value) isConnecting.value = false
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai' && last.streaming) {
        last.text += text
      } else {
        messages.value.push({ role: 'ai', text, streaming: true })
      }
      scrollToBottom()
    },
    onDone(data) {
      isConnecting.value = false
      sessionId.value = data.session_id
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai') {
        last.text = data.full_text
        last.streaming = false
      }
      speakAndListen(data.full_text, data.tts_url ? ttsCachedUrl(data.tts_url) : null)
    },
    onError() {
      isConnecting.value = false
      messages.value.push({ role: 'ai', text: 'Connection failed. Please try again.' })
    },
  })
}

// ========== AI 说话 → 自动听 ==========
async function speakAndListen(text, ttsUrl) {
  if (isPaused.value) return
  callState.value = 'ai_speaking'
  try {
    const url = ttsUrl || ttsStreamUrl(text)
    currentAudio = new Audio(url)
    currentAudio.onended = () => {
      currentAudio = null
      if (!isPaused.value) startListening()
    }
    currentAudio.onerror = () => {
      currentAudio = null
      if (!isPaused.value) startListening()
    }
    await currentAudio.play()
  } catch (e) {
    currentAudio = null
    if (!isPaused.value) startListening()
  }
}

// ========== VAD 录音 ==========
async function startListening() {
  if (isPaused.value || isHangingUp) return
  callState.value = 'listening'
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
      audioContext = null
      if (!isPaused.value) processUserAudio()
    }
    mediaRecorder.start()

    // VAD 检测循环
    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    let silenceStart = null
    let hasVoice = false  // 是否检测到过语音

    function checkVolume() {
      if (callState.value !== 'listening' || isPaused.value) return
      analyser.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128
        sum += v * v
      }
      const rms = Math.sqrt(sum / dataArray.length)

      if (rms < SILENCE_THRESHOLD) {
        // 只有检测到过语音后，才开始计时静音
        if (hasVoice) {
          if (!silenceStart) silenceStart = Date.now()
          else if (Date.now() - silenceStart > SILENCE_DURATION) {
            if (mediaRecorder?.state === 'recording') {
              mediaRecorder.stop()
            }
            return
          }
        }
      } else {
        hasVoice = true
        silenceStart = null
      }
      vadRaF = requestAnimationFrame(checkVolume)
    }
    vadRaF = requestAnimationFrame(checkVolume)
  } catch (e) {
    console.error('麦克风访问失败:', e)
    callState.value = 'idle'
  }
}

async function processUserAudio() {
  if (isPaused.value || isHangingUp) return
  if (audioChunks.length === 0) {
    startListening()
    return
  }

  callState.value = 'thinking'
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })

  streamSpeakConversation(sessionId.value, selectedScenario.value.id, audioBlob, {
    onAsr(text) {
      const idx = messages.value.push({ role: 'user', text: '' }) - 1
      currentUserMsgIdx = idx
      scrollToBottom()
      // 逐字流式显示用户文本
      typewriteUserText(idx, text)
    },
    onGrammar(data) {
      // 语法纠错挂到对应索引的用户消息上
      if (currentUserMsgIdx >= 0 && currentUserMsgIdx < messages.value.length) {
        const msg = messages.value[currentUserMsgIdx]
        if (msg && msg.role === 'user') {
          msg.grammar = { ...data, _collapsed: true }
        }
      }
    },
    onToken(text) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai' && last.streaming) {
        last.text += text
      } else {
        messages.value.push({ role: 'ai', text, streaming: true })
      }
      scrollToBottom()
    },
    onDone(data) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai') {
        last.text = data.full_text
        last.streaming = false
      }
      speakAndListen(data.full_text, data.tts_url ? ttsCachedUrl(data.tts_url) : null)
    },
    onError() {
      messages.value.push({ role: 'ai', text: 'Sorry, I had trouble understanding that.' })
      scrollToBottom()
      startListening()
    },
  })
}

// ========== 暂停 / 继续 ==========
function togglePause() {
  if (isPaused.value) {
    // 继续对话
    isPaused.value = false
    if (currentAudio) {
      currentAudio.play()
      callState.value = 'ai_speaking'
    } else {
      startListening()
    }
  } else {
    // 暂停对话
    isPaused.value = true
    if (currentAudio) currentAudio.pause()
    if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
    if (vadRaF) { cancelAnimationFrame(vadRaF); vadRaF = null }
    callState.value = 'paused'
  }
}

// ========== 挂断 ==========
async function hangUp() {
  isHangingUp = true
  isPaused.value = false

  // 1. 停止录音和相关资源
  if (vadRaF) { cancelAnimationFrame(vadRaF); vadRaF = null }
  if (mediaRecorder) {
    // 移除 onstop 回调，防止触发 processUserAudio
    mediaRecorder.onstop = null
    if (mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }
    // 立即释放麦克风
    if (mediaRecorder.stream) {
      mediaRecorder.stream.getTracks().forEach(t => t.stop())
    }
    mediaRecorder = null
  }
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }

  // 2. 停止 AI 音频播放
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.src = ''
    currentAudio = null
  }
  if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null }

  callState.value = 'idle'

  // 获取评分报告
  if (sessionId.value) {
    isScoring.value = true
    phase.value = 'report'  // 立即切换页面，显示加载状态
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
  messages.value = []
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
            <template v-else-if="callState === 'paused'">
              <span class="state-dot paused"></span> 已暂停
            </template>
            <template v-else>准备就绪</template>
          </div>
        </div>

        <!-- 底部字幕区 → 滚动聊天记录 -->
        <div class="call-chat-box" ref="chatBoxRef">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="chat-bubble"
            :class="msg.role"
          >
            <span class="bubble-avatar" v-if="msg.role === 'user'">
                <el-avatar :size="32" :src="authStore.userInfo?.avatar" icon="UserFilled" />
              </span>
              <span class="bubble-avatar" v-else>🐱</span>
            <div class="bubble-content">
              <p class="bubble-text">{{ msg.text }}</p>
              <!-- 语法检测中 -->
              <div
                v-if="!msg.grammar && msg.role === 'user' && idx === currentUserMsgIdx && msg.text && msg.text !== '(未识别到语音)'"
                class="grammar-checking"
              >
                <span class="gck-dot"></span> 语法检测中...
              </div>
              <!-- 语法纠错入口（每条用户消息下方） -->
              <div
                v-if="msg.grammar?.errors?.length"
                class="grammar-indicator"
                :class="{ expanded: !msg.grammar._collapsed }"
                @click="msg.grammar._collapsed = !msg.grammar._collapsed"
              >
                <span class="gi-icon">📝</span>
                <span class="gi-text">{{ msg.grammar._collapsed ? `${msg.grammar.errors.length} 个语法提示` : '收起语法提示' }}</span>
                <span class="gi-count">{{ msg.grammar.errors.length }}</span>
                <span class="gi-arrow">▾</span>
              </div>
              <!-- 语法纠错详情 -->
              <div v-if="msg.grammar?.errors?.length && !msg.grammar._collapsed" class="grammar-correction-card">
                <div class="gc-corrected" v-if="msg.grammar.corrected_text !== msg.grammar.original_text">
                  <span class="gc-label">修正：</span>
                  <span class="gc-corrected-text">{{ msg.grammar.corrected_text }}</span>
                </div>
                <div v-for="(err, i) in msg.grammar.errors" :key="i" class="gc-error-item">
                  <span class="gc-error-original">{{ err.original }}</span>
                  <span class="gc-error-arrow">→</span>
                  <span class="gc-error-correction">{{ err.correction }}</span>
                  <span
                    class="gc-error-type"
                    :style="{ background: ERROR_TYPE_COLORS[err.error_type] || '#909399' }"
                  >{{ ERROR_TYPE_LABELS[err.error_type] || err.error_type }}</span>
                  <span class="gc-error-explain">{{ err.explanation }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- 思考中指示器 -->
          <div v-if="callState === 'thinking'" class="chat-bubble ai thinking">
            <span class="bubble-avatar">🐱</span>
            <div class="bubble-content">
              <span class="thinking-dots">...</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="call-actions">
          <button class="pause-btn" @click="togglePause">
            <span class="pause-icon">{{ isPaused ? '▶️' : '⏸️' }}</span>
          </button>
          <p class="pause-label">{{ isPaused ? '继续' : '暂停' }}</p>
          <button class="hangup-btn" @click="hangUp">
            <span class="hangup-icon">📞</span>
          </button>
          <p class="hangup-label">挂断</p>
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
            <h2>对话报告</h2>
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
              <h2>对话报告</h2>
              <p class="report-scene">{{ selectedScenario?.emoji }} {{ selectedScenario?.title }} 场景</p>
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

            <!-- 右列：文本评测 -->
            <section class="report-card" v-if="scoreReport.text_dimension_details?.length">
              <div class="card-title">
                <span class="card-icon">📝</span> 文本评测（LLM）
              </div>
              <div class="text-dim-cards">
                <div v-for="dim in scoreReport.text_dimension_details" :key="dim.label" class="text-dim-card">
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

          <!-- 流利度评估（SRS 3.3.3） -->
          <section class="report-card report-card--full" v-if="scoreReport.fluency?.rounds?.length">
            <div class="card-title">
              <span class="card-icon">🌊</span> 流利度评估
              <span class="fluency-badge" :class="'grade-' + scoreReport.fluency.grade">
                {{ scoreReport.fluency.grade }}
              </span>
              <span class="fluency-overall">综合 {{ scoreReport.fluency.overall }} 分</span>
            </div>

            <!-- 每轮明细 -->
            <div class="fluency-rounds">
              <div
                v-for="round in scoreReport.fluency.rounds"
                :key="round.round"
                class="fluency-round-card"
                :class="{ 'best-round': round.round === scoreReport.fluency.best_round }"
              >
                <div class="fr-header">
                  <span class="fr-label">第 {{ round.round }} 轮</span>
                  <span v-if="round.round === scoreReport.fluency.best_round" class="fr-best">⭐ 最佳</span>
                  <span class="fr-total">{{ round.total }} 分</span>
                </div>
                <div class="fr-text">{{ round.text?.slice(0, 80) }}{{ round.text?.length > 80 ? '...' : '' }}</div>
                <div class="fr-dims">
                  <div class="fr-dim">
                    <span class="fd-label">语速</span>
                    <span class="fd-value" :style="{ color: dimScoreColor(round.wpm?.score) }">{{ round.wpm?.score }}/25</span>
                    <span class="fd-detail">{{ round.wpm?.value }} wpm</span>
                  </div>
                  <div class="fr-dim">
                    <span class="fd-label">停顿</span>
                    <span class="fd-value" :style="{ color: dimScoreColor(round.pause_frequency?.score * 5) }">{{ round.pause_frequency?.score }}/20</span>
                    <span class="fd-detail">{{ round.pause_frequency?.pauses_per_min }}次/分</span>
                  </div>
                  <div class="fr-dim">
                    <span class="fd-label">重复</span>
                    <span class="fd-value" :style="{ color: dimScoreColor(round.repetition?.score * 5) }">{{ round.repetition?.score }}/20</span>
                    <span class="fd-detail">{{ (round.repetition?.rate * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="fr-dim">
                    <span class="fd-label">语法</span>
                    <span class="fd-value" :style="{ color: dimScoreColor(round.grammar?.score * 5) }">{{ round.grammar?.score || '—' }}/20</span>
                    <span class="fd-detail" v-if="round.grammar?.errors?.length">{{ round.grammar.errors.length }} 个错误</span>
                  </div>
                  <div class="fr-dim">
                    <span class="fd-label">相关性</span>
                    <span class="fd-value" :style="{ color: dimScoreColor(round.relevance?.score / 15 * 100) }">{{ round.relevance?.score || '—' }}/15</span>
                    <span class="fd-detail" v-if="round.relevance?.note">{{ round.relevance.note }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="fluency-suggestions" v-if="scoreReport.fluency.suggestions">
              💡 {{ scoreReport.fluency.suggestions }}
            </div>
          </section>

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
                  <template v-if="msg.role === 'grammar'">
                    <div class="transcript-role">📝 语法纠错</div>
                    <div class="transcript-grammar">
                      <div class="tg-corrected" v-if="msg.text.corrected_text !== msg.text.original_text">
                        <span class="tg-label">修正：</span>
                        <span class="tg-corrected-text">{{ msg.text.corrected_text }}</span>
                      </div>
                      <div v-for="(err, i) in msg.text.errors" :key="i" class="tg-error">
                        <span class="tg-error-original">{{ err.original }}</span>
                        <span>→</span>
                        <span class="tg-error-correction">{{ err.correction }}</span>
                        <span class="tg-error-type" :style="{ background: ERROR_TYPE_COLORS[err.error_type] || '#909399' }">{{ ERROR_TYPE_LABELS[err.error_type] || err.error_type }}</span>
                        <span class="tg-error-explain">{{ err.explanation }}</span>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="transcript-role">{{ msg.role === 'user' ? '😊 你' : '🐱 AI' }}</div>
                    <div class="transcript-bubble">{{ msg.text }}</div>
                  </template>
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
            <button class="retry-btn" @click="selectScenario(selectedScenario)">
              <span>🔄</span> 再来一次
            </button>
            <button class="back-btn" @click="backToScenes">
              <span>🏠</span> 返回场景
            </button>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.voice-call-page {
  min-height: calc(100vh - 56px);
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
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 28px 20px;
  max-width: 900px;
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
  min-height: calc(100vh - 56px);
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
    &.paused {
      background: #909399;
    }
  }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

// 聊天记录滚动区
.call-chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(100vh - 360px);
  min-height: 0;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #E0D8F0; border-radius: 2px; }
}

.chat-bubble {
  display: flex;
  gap: 8px;
  max-width: 80%;
  animation: bubbleIn 0.3s ease;

  .bubble-avatar {
    font-size: 22px;
    flex-shrink: 0;
    line-height: 1;
    margin-top: 4px;
  }
  .bubble-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .bubble-text {
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.5;
    margin: 0;
    color: #4A4A5A;
  }

  &.user {
    align-self: flex-end;
    flex-direction: row-reverse;
    .bubble-text {
      background: #F0F0FF;
      border-bottom-right-radius: 4px;
      text-align: left;
    }
  }
  &.ai {
    align-self: flex-start;
    .bubble-text {
      background: #FFF0F3;
      border-bottom-left-radius: 4px;
    }
    &.thinking .bubble-text {
      background: #FFF0F3;
      .thinking-dots {
        animation: dotPulse 1.2s infinite;
        font-size: 18px;
        letter-spacing: 2px;
      }
    }
  }
}

@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

// 操作按钮
.call-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 16px 20px 36px;
  flex-shrink: 0;
}

.pause-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  background: #F0E8FF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
  .pause-icon { font-size: 20px; }
  &:hover { background: #E0D0FF; transform: scale(1.05); }
  &:active { transform: scale(0.95); }
}

.pause-label {
  font-size: 11px;
  color: #bbb;
  margin: 0;
  text-align: center;
}

.hangup-btn {
  width: 52px;
  height: 52px;
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
    font-size: 22px;
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
  font-size: 11px;
  color: #bbb;
  margin: 0;
  text-align: center;
}

// 语法检测中
.grammar-checking {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #B45309;
  margin-top: 4px;
  .gck-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #F59E0B;
    animation: pulse-dot 0.8s ease-in-out infinite;
  }
}

// 语法纠错入口指示器
.grammar-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: 14px;
  cursor: pointer;
  font-size: 11px;
  color: #92400E;
  user-select: none;
  transition: all 0.2s;
  margin-top: 4px;

  &:hover { background: #FEF3C7; }
  &.expanded { border-radius: 14px 14px 0 0; border-bottom: none; }

  .gi-icon { font-size: 12px; }
  .gi-text { flex: 1; }
  .gi-count {
    background: #F59E0B;
    color: #fff;
    border-radius: 10px;
    padding: 0 6px;
    font-size: 10px;
    font-weight: 600;
    min-width: 16px;
    text-align: center;
  }
  .gi-arrow {
    font-size: 10px;
    transition: transform 0.2s;
    color: #B45309;
  }
  &.expanded .gi-arrow { transform: rotate(180deg); }
}

// 语法纠错卡片
.grammar-correction-card {
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-top: none;
  border-radius: 0 0 14px 14px;
  padding: 8px 12px 10px;
  margin-top: -1px;
  animation: gcSlideIn 0.2s ease;
}

@keyframes gcSlideIn {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 300px; }
}

.gc-corrected {
  display: flex;
  gap: 6px;
  padding: 6px 0;
  margin-bottom: 4px;
  border-bottom: 1px dashed #FDE68A;
  .gc-label { font-size: 11px; color: #92400E; font-weight: 600; flex-shrink: 0; }
  .gc-corrected-text { font-size: 12px; color: #4A4A5A; line-height: 1.5; }
}

.gc-error-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 0;
  flex-wrap: wrap;
  & + & { border-top: 1px solid #FEF3C7; }
  .gc-error-original {
    font-size: 11px; color: #DC2626; text-decoration: line-through;
    background: #FEE2E2; padding: 1px 5px; border-radius: 4px;
  }
  .gc-error-arrow { font-size: 10px; color: #999; }
  .gc-error-correction {
    font-size: 11px; color: #059669; font-weight: 600;
    background: #D1FAE5; padding: 1px 5px; border-radius: 4px;
  }
  .gc-error-type {
    font-size: 10px; color: #fff; padding: 1px 5px; border-radius: 8px;
    font-weight: 500; flex-shrink: 0;
  }
  .gc-error-explain {
    font-size: 11px; color: #999; width: 100%; margin-top: 2px;
    padding-left: 2px;
  }
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
  .report-scene { font-size: 13px; color: #999; margin-top: 4px; }
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
  &.grammar { align-self: flex-start; }
  .transcript-role { font-size: 10px; color: #999; margin-bottom: 2px; padding: 0 4px; }
  &.user .transcript-role { text-align: right; }
  .transcript-bubble {
    padding: 8px 12px; border-radius: 12px; font-size: 12px; line-height: 1.5; color: #4A4A5A;
  }
  &.user .transcript-bubble { background: #F0F0FF; border-bottom-right-radius: 4px; }
  &.ai .transcript-bubble { background: #FFF0F3; border-bottom-left-radius: 4px; }
}

// 报告中的语法纠错
.transcript-grammar {
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 11px;
  .tg-corrected {
    display: flex; gap: 4px; margin-bottom: 6px; padding-bottom: 6px;
    border-bottom: 1px dashed #FDE68A;
    .tg-label { color: #92400E; font-weight: 600; flex-shrink: 0; }
    .tg-corrected-text { color: #4A4A5A; }
  }
  .tg-error {
    display: flex; align-items: center; gap: 4px; padding: 3px 0; flex-wrap: wrap;
    font-size: 11px; color: #666;
    .tg-error-original { color: #DC2626; text-decoration: line-through; background: #FEE2E2; padding: 0 4px; border-radius: 3px; }
    .tg-error-correction { color: #059669; font-weight: 600; background: #D1FAE5; padding: 0 4px; border-radius: 3px; }
    .tg-error-type { font-size: 10px; color: #fff; padding: 0 5px; border-radius: 8px; }
    .tg-error-explain { width: 100%; color: #999; font-size: 10px; margin-top: 1px; }
  }
}

// 建议
.suggestions-content {
  p { font-size: 13px; color: #666; line-height: 1.7; margin: 0; }
}

// ========== 流利度评估 ==========
.fluency-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 8px;
  &.grade-优秀 { background: #E8F8F0; color: #3EC790; }
  &.grade-良好 { background: #E8F0FF; color: #5B8DEF; }
  &.grade-中等 { background: #FFF8E8; color: #F0A030; }
  &.grade-初级 { background: #FFF0E8; color: #F08040; }
  &.grade-入门 { background: #FFE8E8; color: #E05050; }
}
.fluency-overall {
  font-size: 13px;
  color: #888;
  margin-left: auto;
}
.fluency-rounds {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}
.fluency-round-card {
  background: #FAFBFC;
  border: 1px solid #EBEEF5;
  border-radius: 10px;
  padding: 12px 16px;
  &.best-round {
    border-color: #F6BD16;
    background: #FFFDF5;
  }
}
.fr-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.fr-label { font-size: 13px; font-weight: 600; color: #555; }
.fr-best { font-size: 11px; color: #F0A030; }
.fr-total { font-size: 14px; font-weight: 700; color: #4A4A5A; margin-left: auto; }
.fr-text {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
  font-style: italic;
  line-height: 1.5;
}
.fr-dims {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.fr-dim {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  min-width: 70px;
  border: 1px solid #F0F0F0;
}
.fd-label { font-size: 11px; color: #999; margin-bottom: 2px; }
.fd-value { font-size: 15px; font-weight: 700; }
.fd-detail { font-size: 10px; color: #bbb; margin-top: 2px; }
.fluency-suggestions {
  margin-top: 14px;
  padding: 12px;
  background: #F0F8FF;
  border-radius: 8px;
  font-size: 13px;
  color: #5B8DEF;
  line-height: 1.6;
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