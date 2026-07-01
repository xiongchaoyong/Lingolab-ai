<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { streamStartRoleplay, streamSpeakRoleplay, ttsStreamUrl, ttsCachedUrl, endRoleplay } from '@/api/roleplay'
import UtteranceDetailPanel from '@/components/pronunciation/UtteranceDetailPanel.vue'

const router = useRouter()

const ROLES = [
  { id: 'interviewee', title: '面试者', subtitle: 'AI 扮演面试官', emoji: '💼', color: '#A78BFA' },
  { id: 'waiter', title: '服务员', subtitle: 'AI 扮演顾客', emoji: '🍽️', color: '#5AD8A6' },
  { id: 'guide', title: '导游', subtitle: 'AI 扮演游客', emoji: '🗺️', color: '#5B8FF9' },
  { id: 'doctor', title: '医生', subtitle: 'AI 扮演患者', emoji: '🩺', color: '#E74C3C' },
  { id: 'teacher', title: '老师', subtitle: 'AI 扮演学生', emoji: '📚', color: '#F39C12' },
  { id: 'customer_service', title: '客服', subtitle: 'AI 扮演顾客', emoji: '📞', color: '#3498DB' },
  { id: 'receptionist', title: '前台接待', subtitle: 'AI 扮演酒店客人', emoji: '🛎️', color: '#1ABC9C' },
  { id: 'colleague', title: '同事', subtitle: 'AI 扮演新同事', emoji: '🤝', color: '#9B59B6' },
]

const phase = ref('select')
const selectedRole = ref(null)
const sessionId = ref('')
const callState = ref('idle')
const isConnecting = ref(false)
const isPaused = ref(false)
const scoreReport = ref(null)
const isScoring = ref(false)

const messages = ref([])
const chatBoxRef = ref(null)
let activeStreamController = null  // 当前活跃的 SSE 流控制器，新请求取消旧请求
const currentUserMsgIdx = ref(-1)  // 模板渲染用（哪个消息正在等待语法检测）

const ERROR_TYPE_COLORS = {
  tense: '#E6A23C', subject_verb_agreement: '#F56C6C', article: '#909399',
  preposition: '#67C23A', word_order: '#409EFF', plural: '#E6A23C',
  word_choice: '#9B59B6', other: '#909399',
}
const ERROR_TYPE_LABELS = {
  tense: '时态', subject_verb_agreement: '主谓一致', article: '冠词',
  preposition: '介词', word_order: '语序', plural: '复数',
  word_choice: '用词', other: '其他',
}

const hasDetailedReport = computed(() => scoreReport.value?.utterances?.length > 0)
const aggregatedErrors = computed(() => {
  if (!scoreReport.value?.utterances) return []
  const errorMap = new Map()
  for (const utt of scoreReport.value.utterances) {
    for (const err of utt.errors || []) {
      const key = err.phoneme
      if (!errorMap.has(key) || errorMap.get(key).score > err.score) errorMap.set(key, err)
    }
  }
  return [...errorMap.values()].sort((a, b) => a.score - b.score)
})

const expandedUtterance = ref(null)
function toggleUtterance(index) { expandedUtterance.value = expandedUtterance.value === index ? null : index }

async function scrollToBottom() {
  await nextTick()
  if (chatBoxRef.value) chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
}

function typewriteUserText(idx, fullText) {
  let pos = 0
  const speed = 15
  function step() {
    if (isHangingUp) return
    if (pos < fullText.length && idx < messages.value.length) {
      messages.value[idx].text = fullText.slice(0, ++pos)
      scrollToBottom()
      setTimeout(step, speed * (Math.random() * 0.5 + 0.75))
    }
  }
  step()
}

let audioContext = null
let analyser = null
let mediaRecorder = null
let audioChunks = []
let silenceTimer = null
let currentAudio = null
let vadRaF = null
let isHangingUp = false
const SILENCE_THRESHOLD = 0.02
const SILENCE_DURATION = 2500

async function selectRole(role) {
  selectedRole.value = role
  phase.value = 'calling'
  callState.value = 'idle'
  isPaused.value = false
  messages.value = []
  if (activeStreamController) { activeStreamController.abort(); activeStreamController = null }
  currentUserMsgIdx.value = -1

  isConnecting.value = true
  streamStartRoleplay(role.id, 'B1', {
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
      if (last && last.role === 'ai') { last.text = data.full_text; last.streaming = false }
      speakAndListen(data.full_text, data.tts_url ? ttsCachedUrl(data.tts_url) : null)
    },
    onError() {
      isConnecting.value = false
      messages.value.push({ role: 'ai', text: 'Connection failed. Please try again.' })
    },
  })
}

async function speakAndListen(text, ttsUrl) {
  if (isPaused.value) return
  callState.value = 'ai_speaking'
  try {
    const url = ttsUrl || ttsStreamUrl(text)
    currentAudio = new Audio(url)
    currentAudio.onended = () => { currentAudio = null; if (!isPaused.value) startListening() }
    currentAudio.onerror = () => { currentAudio = null; if (!isPaused.value) startListening() }
    await currentAudio.play()
  } catch (e) { currentAudio = null; if (!isPaused.value) startListening() }
}

async function startListening() {
  if (isPaused.value || isHangingUp) return
  callState.value = 'listening'
  audioChunks = []

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1 } })
    audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data) }
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop())
      audioContext.close(); audioContext = null
      if (!isPaused.value) processUserAudio()
    }
    mediaRecorder.start()

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    let silenceStart = null
    let hasVoice = false

    function checkVolume() {
      if (callState.value !== 'listening' || isPaused.value) return
      analyser.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) { const v = (dataArray[i] - 128) / 128; sum += v * v }
      const rms = Math.sqrt(sum / dataArray.length)
      if (rms < SILENCE_THRESHOLD) {
        if (hasVoice) {
          if (!silenceStart) silenceStart = Date.now()
          else if (Date.now() - silenceStart > SILENCE_DURATION) {
            if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
            return
          }
        }
      } else { hasVoice = true; silenceStart = null }
      vadRaF = requestAnimationFrame(checkVolume)
    }
    vadRaF = requestAnimationFrame(checkVolume)
  } catch (e) { console.error('麦克风访问失败:', e); callState.value = 'idle' }
}

async function processUserAudio() {
  if (isPaused.value || isHangingUp) return
  if (audioChunks.length === 0) { startListening(); return }

  callState.value = 'thinking'
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })

  // 取消上一次 SSE 流（避免旧语法检测结果覆盖新消息）
  if (activeStreamController) {
    activeStreamController.abort()
  }
  activeStreamController = new AbortController()
  const signal = activeStreamController.signal
  let msgIdx = -1  // 局部变量：每次调用独立的索引，避免竞态覆盖

  streamSpeakRoleplay(sessionId.value, selectedRole.value.id, audioBlob, {
    onAsr(text) {
      msgIdx = messages.value.push({ role: 'user', text: '' }) - 1
      currentUserMsgIdx.value = msgIdx  // 模板渲染用
      scrollToBottom()
      typewriteUserText(msgIdx, text)
    },
    onGrammar(data) {
      // 使用闭包捕获的 msgIdx，不会被后续调用覆盖
      if (msgIdx >= 0 && msgIdx < messages.value.length) {
        const msg = messages.value[msgIdx]
        if (msg && msg.role === 'user') msg.grammar = { ...data, _collapsed: true }
      }
    },
    onToken(text) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai' && last.streaming) last.text += text
      else messages.value.push({ role: 'ai', text, streaming: true })
      scrollToBottom()
    },
    onDone(data) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'ai') { last.text = data.full_text; last.streaming = false }
      if (data.conversation_complete) { setTimeout(() => hangUp(), 500) }
      else speakAndListen(data.full_text, data.tts_url ? ttsCachedUrl(data.tts_url) : null)
    },
    onError() {
      messages.value.push({ role: 'ai', text: 'Sorry, I had trouble understanding that.' })
      scrollToBottom(); startListening()
    },
  }, signal)
}

function togglePause() {
  if (isPaused.value) {
    isPaused.value = false
    if (currentAudio) { currentAudio.play(); callState.value = 'ai_speaking' }
    else startListening()
  } else {
    isPaused.value = true
    if (currentAudio) currentAudio.pause()
    if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
    if (vadRaF) { cancelAnimationFrame(vadRaF); vadRaF = null }
    callState.value = 'paused'
  }
}

async function hangUp() {
  isHangingUp = true; isPaused.value = false
  // 取消进行中的 SSE 流
  if (activeStreamController) { activeStreamController.abort(); activeStreamController = null }
  if (vadRaF) { cancelAnimationFrame(vadRaF); vadRaF = null }
  if (mediaRecorder) {
    mediaRecorder.onstop = null
    if (mediaRecorder.state === 'recording') mediaRecorder.stop()
    if (mediaRecorder.stream) mediaRecorder.stream.getTracks().forEach(t => t.stop())
    mediaRecorder = null
  }
  if (audioContext) { audioContext.close(); audioContext = null }
  if (currentAudio) { currentAudio.pause(); currentAudio.src = ''; currentAudio = null }
  if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null }
  callState.value = 'idle'

  if (sessionId.value) {
    isScoring.value = true; phase.value = 'report'
    try { scoreReport.value = await endRoleplay(sessionId.value) }
    catch (e) {
      scoreReport.value = {
        overall: 0, pronunciation: [], dimensions: [], dimension_details: [],
        suggestions: '评分服务暂时异常，请稍后重试', utterances: [], transcript: [],
        scoring_methodology: '',
      }
    }
    isScoring.value = false; phase.value = 'report'
  } else { phase.value = 'select'; resetCall() }
}

function resetCall() {
  selectedRole.value = null; callState.value = 'idle'; messages.value = []
  scoreReport.value = null; sessionId.value = ''
}
function backToRoles() { phase.value = 'select'; resetCall() }
function goBack() { router.push('/home') }

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

onUnmounted(() => { hangUp() })
</script>

<template>
  <div class="roleplay-page">
    <template v-if="phase === 'select'">
      <div class="rp-select-header">
        <div class="header-mascot">🎭</div>
        <h2>情景角色扮演</h2>
        <p class="select-subtitle">选一个角色，和 AI 进行真实语音对话吧~</p>
      </div>
      <div class="rp-role-grid">
        <div v-for="role in ROLES" :key="role.id" class="rp-role-card"
          :style="{ '--accent': role.color }" @click="selectRole(role)">
          <div class="rrc-emoji">{{ role.emoji }}</div>
          <h4>{{ role.title }}</h4>
          <p>{{ role.subtitle }}</p>
        </div>
      </div>
      <div class="select-footer">
        <el-button text @click="goBack" class="back-btn"><el-icon><ArrowLeft /></el-icon> 返回首页</el-button>
      </div>
    </template>

    <template v-else-if="phase === 'calling'">
      <div class="call-screen">
        <div class="call-top">
          <div class="call-role-pill">
            <span class="pill-emoji">{{ selectedRole?.emoji }}</span>
            {{ selectedRole?.title }}
          </div>
        </div>

        <div class="call-center">
          <div class="mascot-container" :class="callState">
            <div class="ripple-ring r1"></div><div class="ripple-ring r2"></div><div class="ripple-ring r3"></div>
            <div class="mascot-avatar"><span class="mascot-face">{{ selectedRole?.emoji }}</span></div>
          </div>
          <div class="call-state-label" :class="callState">
            <template v-if="isConnecting">正在连接...</template>
            <template v-else-if="callState === 'ai_speaking'"><span class="state-dot speaking"></span> AI 正在说话</template>
            <template v-else-if="callState === 'listening'"><span class="state-dot listening"></span> 正在聆听...</template>
            <template v-else-if="callState === 'thinking'"><span class="state-dot thinking"></span> 思考中...</template>
            <template v-else-if="callState === 'paused'"><span class="state-dot paused"></span> 已暂停</template>
            <template v-else>准备就绪</template>
          </div>
        </div>

        <div class="call-chat-box" ref="chatBoxRef">
          <div v-for="(msg, idx) in messages" :key="idx" class="chat-bubble" :class="msg.role">
            <span class="bubble-avatar">{{ msg.role === 'user' ? '😊' : selectedRole?.emoji }}</span>
            <div class="bubble-content">
              <p class="bubble-text">{{ msg.text }}</p>
              <div v-if="!msg.grammar && msg.role === 'user' && idx === currentUserMsgIdx && msg.text && msg.text !== '(未识别到语音)'" class="grammar-checking">
                <span class="gck-dot"></span> 语法检测中...
              </div>
              <div v-if="msg.grammar?.errors?.length" class="grammar-indicator"
                :class="{ expanded: !msg.grammar._collapsed }"
                @click="msg.grammar._collapsed = !msg.grammar._collapsed">
                <span class="gi-icon">📝</span>
                <span class="gi-text">{{ msg.grammar._collapsed ? `${msg.grammar.errors.length} 个语法提示` : '收起语法提示' }}</span>
                <span class="gi-count">{{ msg.grammar.errors.length }}</span>
                <span class="gi-arrow">▾</span>
              </div>
              <div v-if="msg.grammar?.errors?.length && !msg.grammar._collapsed" class="grammar-correction-card">
                <div class="gc-corrected" v-if="msg.grammar.corrected_text !== msg.grammar.original_text">
                  <span class="gc-label">修正：</span><span class="gc-corrected-text">{{ msg.grammar.corrected_text }}</span>
                </div>
                <div v-for="(err, i) in msg.grammar.errors" :key="i" class="gc-error-item">
                  <span class="gc-error-original">{{ err.original }}</span>
                  <span class="gc-error-arrow">→</span>
                  <span class="gc-error-correction">{{ err.correction }}</span>
                  <span class="gc-error-type" :style="{ background: ERROR_TYPE_COLORS[err.error_type] || '#909399' }">{{ ERROR_TYPE_LABELS[err.error_type] || err.error_type }}</span>
                  <span class="gc-error-explain">{{ err.explanation }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="callState === 'thinking'" class="chat-bubble ai thinking">
            <span class="bubble-avatar">{{ selectedRole?.emoji }}</span>
            <div class="bubble-content"><span class="thinking-dots">...</span></div>
          </div>
        </div>

        <div class="call-actions">
          <button class="pause-btn" @click="togglePause"><span class="pause-icon">{{ isPaused ? '▶️' : '⏸️' }}</span></button>
          <p class="pause-label">{{ isPaused ? '继续' : '暂停' }}</p>
          <button class="hangup-btn" @click="hangUp"><span class="hangup-icon">📞</span></button>
          <p class="hangup-label">挂断</p>
        </div>
      </div>
    </template>

    <template v-else-if="phase === 'report'">
      <div class="report-screen">
        <template v-if="isScoring || !scoreReport">
          <div class="report-header"><div class="report-mascot">🌟</div><h2>角色扮演报告</h2></div>
          <div class="report-loading"><div class="loading-spinner"></div><p>正在生成报告...</p></div>
        </template>
        <template v-else>
          <div class="report-top">
            <div class="report-header">
              <div class="report-mascot">🌟</div><h2>角色扮演报告</h2>
              <p class="report-role">{{ selectedRole?.emoji }} {{ selectedRole?.title }} 角色</p>
            </div>
            <div class="overall-area">
              <div class="overall-circle">
                <span class="overall-num">{{ scoreReport.overall }}</span>
                <span class="overall-unit">分</span>
                <span class="overall-level">{{ scoreReport.overall >= 80 ? '🎉 优秀' : scoreReport.overall >= 60 ? '👍 良好' : '💪 加油' }}</span>
              </div>
              <div class="methodology-card" v-if="scoreReport.scoring_methodology">
                <div class="methodology-title">📐 评分计算方式</div>
                <pre class="methodology-text">{{ scoreReport.scoring_methodology }}</pre>
              </div>
            </div>
          </div>
          <div class="report-main">
            <section class="report-card" v-if="scoreReport.pronunciation?.length">
              <div class="card-title"><span class="card-icon">🎤</span> 语音评测</div>
              <div class="dimension-list">
                <div v-for="dim in scoreReport.pronunciation" :key="dim.label" class="dimension-item">
                  <div class="dim-header"><span class="dim-label">{{ dim.label }}</span><span class="dim-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span></div>
                  <div class="dim-bar-bg"><div class="dim-bar-fill" :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"></div></div>
                </div>
              </div>
              <div class="error-section" v-if="aggregatedErrors.length > 0">
                <div class="error-title">⚠️ 问题音素</div>
                <div v-for="err in aggregatedErrors" :key="err.phoneme" class="error-item">
                  <el-tag type="danger" size="small">{{ err.phoneme }}</el-tag>
                  <span class="error-actual">{{ err.actual }}</span><span class="error-tip-text">{{ err.tip }}</span>
                </div>
              </div>
            </section>
            <section class="report-card" v-if="scoreReport.dimension_details?.length">
              <div class="card-title"><span class="card-icon">🎭</span> 角色表现评测（LLM）</div>
              <div class="text-dim-cards">
                <div v-for="dim in scoreReport.dimension_details" :key="dim.label" class="text-dim-card">
                  <div class="tdc-header"><span class="tdc-label">{{ dim.label }}</span><span class="tdc-score" :style="{ color: dimScoreColor(dim.score) }">{{ dim.score }}</span></div>
                  <div class="dim-bar-bg" style="margin-bottom: 8px;"><div class="dim-bar-fill" :style="{ width: dim.score + '%', background: dimBarColor(dim.score) }"></div></div>
                  <div class="tdc-feedback" v-if="dim.feedback">{{ dim.feedback }}</div>
                  <div class="tdc-tags">
                    <span v-if="dim.strengths" class="tdc-tag good">✅ {{ dim.strengths }}</span>
                    <span v-if="dim.weaknesses" class="tdc-tag improve">📌 {{ dim.weaknesses }}</span>
                  </div>
                </div>
              </div>
            </section>
          </div>
          <section class="report-card report-card--full" v-if="scoreReport.fluency?.rounds?.length">
            <div class="card-title"><span class="card-icon">🌊</span> 流利度评估
              <span class="fluency-badge" :class="'grade-' + scoreReport.fluency.grade">{{ scoreReport.fluency.grade }}</span>
              <span class="fluency-overall">综合 {{ scoreReport.fluency.overall }} 分</span>
            </div>
            <div class="fluency-rounds">
              <div v-for="round in scoreReport.fluency.rounds" :key="round.round" class="fluency-round-card" :class="{ 'best-round': round.round === scoreReport.fluency.best_round }">
                <div class="fr-header"><span class="fr-label">第 {{ round.round }} 轮</span><span v-if="round.round === scoreReport.fluency.best_round" class="fr-best">⭐ 最佳</span><span class="fr-total">{{ round.total }} 分</span></div>
                <div class="fr-text">{{ round.text?.slice(0, 80) }}{{ round.text?.length > 80 ? '...' : '' }}</div>
                <div class="fr-dims">
                  <div class="fr-dim"><span class="fd-label">语速</span><span class="fd-value" :style="{ color: dimScoreColor(round.wpm?.score) }">{{ round.wpm?.score }}/25</span><span class="fd-detail">{{ round.wpm?.value }} wpm</span></div>
                  <div class="fr-dim"><span class="fd-label">停顿</span><span class="fd-value" :style="{ color: dimScoreColor(round.pause_frequency?.score * 5) }">{{ round.pause_frequency?.score }}/20</span><span class="fd-detail">{{ round.pause_frequency?.pauses_per_min }}次/分</span></div>
                  <div class="fr-dim"><span class="fd-label">重复</span><span class="fd-value" :style="{ color: dimScoreColor(round.repetition?.score * 5) }">{{ round.repetition?.score }}/20</span><span class="fd-detail">{{ (round.repetition?.rate * 100).toFixed(0) }}%</span></div>
                  <div class="fr-dim"><span class="fd-label">语法</span><span class="fd-value" :style="{ color: dimScoreColor(round.grammar?.score * 5) }">{{ round.grammar?.score || '—' }}/20</span><span class="fd-detail" v-if="round.grammar?.errors?.length">{{ round.grammar.errors.length }} 个错误</span></div>
                  <div class="fr-dim"><span class="fd-label">相关性</span><span class="fd-value" :style="{ color: dimScoreColor(round.relevance?.score / 15 * 100) }">{{ round.relevance?.score || '—' }}/15</span><span class="fd-detail" v-if="round.relevance?.note">{{ round.relevance.note }}</span></div>
                </div>
              </div>
            </div>
            <div class="fluency-suggestions" v-if="scoreReport.fluency.suggestions">💡 {{ scoreReport.fluency.suggestions }}</div>
          </section>
          <section class="report-card report-card--full" v-if="hasDetailedReport">
            <div class="card-title"><span class="card-icon">📋</span> 逐句发音分析</div>
            <div class="utterance-grid">
              <div v-for="(utt, idx) in scoreReport.utterances" :key="idx" class="utterance-item" :class="{ expanded: expandedUtterance === idx }">
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
          <div class="report-bottom">
            <section class="report-card" v-if="scoreReport.transcript?.length">
              <div class="card-title"><span class="card-icon">💬</span> 对话记录</div>
              <div class="transcript-list">
                <div v-for="(msg, idx) in scoreReport.transcript" :key="idx" class="transcript-msg" :class="msg.role">
                  <template v-if="msg.role === 'grammar'">
                    <div class="transcript-role">📝 语法纠错</div>
                    <div class="transcript-grammar">
                      <div class="tg-corrected" v-if="msg.text.corrected_text !== msg.text.original_text">
                        <span class="tg-label">修正：</span><span class="tg-corrected-text">{{ msg.text.corrected_text }}</span>
                      </div>
                      <div v-for="(err, i) in msg.text.errors" :key="i" class="tg-error">
                        <span class="tg-error-original">{{ err.original }}</span><span>→</span>
                        <span class="tg-error-correction">{{ err.correction }}</span>
                        <span class="tg-error-type" :style="{ background: ERROR_TYPE_COLORS[err.error_type] || '#909399' }">{{ ERROR_TYPE_LABELS[err.error_type] || err.error_type }}</span>
                        <span class="tg-error-explain">{{ err.explanation }}</span>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="transcript-role">{{ msg.role === 'user' ? '😊 你' : selectedRole?.emoji + ' AI' }}</div>
                    <div class="transcript-bubble">{{ msg.text }}</div>
                  </template>
                </div>
              </div>
            </section>
            <section class="report-card" v-if="scoreReport.suggestions">
              <div class="card-title"><span class="card-icon">💡</span> 改进建议</div>
              <div class="suggestions-content"><p>{{ scoreReport.suggestions }}</p></div>
            </section>
          </div>
          <div class="report-actions">
            <button class="retry-btn" @click="selectRole(selectedRole)"><span>🔄</span> 再来一次</button>
            <button class="back-btn" @click="backToRoles"><span>🏠</span> 返回角色选择</button>
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
  color: #4A4A5A; font-family: 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}
.rp-select-header { text-align: center; padding: 48px 20px 0;
  .header-mascot { font-size: 56px; animation: bounce 2s ease-in-out infinite; display: inline-block; }
  h2 { font-size: 26px; font-weight: 700; margin: 12px 0 8px; color: #3D3D5C; }
  .select-subtitle { color: #999; font-size: 15px; }
}
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.rp-role-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; padding: 28px 20px; max-width: 900px; margin: 0 auto; }
.rp-role-card { background: #fff; border: 2px solid #F0E8FF; border-radius: 20px; padding: 24px 16px; text-align: center; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  &:hover { border-color: var(--accent); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
  .rrc-emoji { font-size: 40px; margin-bottom: 10px; }
  h4 { font-size: 15px; font-weight: 600; margin-bottom: 4px; color: #3D3D5C; }
  p { font-size: 12px; color: #aaa; }
}
.select-footer { text-align: center; padding-bottom: 40px; .back-btn { color: #999; font-size: 14px; } }

.call-screen { display: flex; flex-direction: column; min-height: calc(100vh - 56px); background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 25%, #FFF9F0 50%, #F0F8FF 100%); }
.call-top { text-align: center; padding: 40px 20px 0; }
.call-role-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 500; color: #7C6FF7; background: rgba(124,111,247,0.08); padding: 8px 18px; border-radius: 24px; .pill-emoji { font-size: 16px; } }
.call-center { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 28px; }

.mascot-container { position: relative; width: 140px; height: 140px; display: flex; align-items: center; justify-content: center;
  .ripple-ring { position: absolute; border-radius: 50%; border: 2.5px solid rgba(255,107,138,0.15); animation: none; }
  .r1 { width: 100%; height: 100%; } .r2 { width: 78%; height: 78%; } .r3 { width: 56%; height: 56%; }
  &.ai_speaking .ripple-ring { border-color: rgba(255,107,138,0.25); animation: ripple 1.6s ease-out infinite; }
  &.ai_speaking .r2 { animation-delay: 0.35s; } &.ai_speaking .r3 { animation-delay: 0.7s; }
  &.listening .ripple-ring { border-color: rgba(91,143,249,0.3); animation: ripple 1.3s ease-out infinite; }
  &.listening .r2 { animation-delay: 0.25s; } &.listening .r3 { animation-delay: 0.5s; }
  &.thinking .ripple-ring { border-color: rgba(246,189,22,0.3); animation: ripple 0.9s ease-out infinite; }
  &.thinking .r2 { animation-delay: 0.2s; } &.thinking .r3 { animation-delay: 0.4s; }
  .mascot-avatar { width: 74px; height: 74px; border-radius: 50%; background: linear-gradient(135deg, #FFE0E8, #FFD6E0); display: flex; align-items: center; justify-content: center; z-index: 1; box-shadow: 0 4px 16px rgba(255,107,138,0.15);
    .mascot-face { font-size: 38px; animation: wiggle 3s ease-in-out infinite; }
  }
}
@keyframes ripple { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.7); opacity: 0; } }
@keyframes wiggle { 0%, 100% { transform: rotate(0); } 25% { transform: rotate(5deg); } 75% { transform: rotate(-5deg); } }

.call-state-label { font-size: 16px; color: #999; font-weight: 500; display: flex; align-items: center; gap: 8px;
  .state-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block;
    &.speaking { background: #FF6B8A; animation: pulse-dot 0.8s ease-in-out infinite; }
    &.listening { background: #5B8FF9; animation: pulse-dot 0.8s ease-in-out infinite; }
    &.thinking { background: #F6BD16; animation: pulse-dot 0.5s ease-in-out infinite; }
    &.paused { background: #909399; }
  }
}
@keyframes pulse-dot { 0%, 100% { opacity: 0.4; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } }

.call-chat-box { flex: 1; overflow-y: auto; padding: 12px 20px; display: flex; flex-direction: column; gap: 10px; max-height: calc(100vh - 360px); min-height: 0;
  &::-webkit-scrollbar { width: 4px; } &::-webkit-scrollbar-thumb { background: #E0D8F0; border-radius: 2px; }
}
.chat-bubble { display: flex; gap: 8px; max-width: 80%; animation: bubbleIn 0.3s ease;
  .bubble-avatar { font-size: 22px; flex-shrink: 0; line-height: 1; margin-top: 4px; }
  .bubble-content { display: flex; flex-direction: column; gap: 4px; }
  .bubble-text { padding: 10px 14px; border-radius: 14px; font-size: 18px; font-weight: 600; line-height: 1.5; margin: 0; color: #4A4A5A; }
  &.user { align-self: flex-end; flex-direction: row-reverse;
    .bubble-text { background: #F0F0FF; border-bottom-right-radius: 4px; text-align: left; }
  }
  &.ai { align-self: flex-start;
    .bubble-text { background: #FFF0F3; border-bottom-left-radius: 4px; }
    &.thinking .bubble-text { background: #FFF0F3; .thinking-dots { animation: dotPulse 1.2s infinite; font-size: 18px; letter-spacing: 2px; } }
  }
}
@keyframes bubbleIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes dotPulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }

.grammar-checking { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: #B45309; margin-top: 4px;
  .gck-dot { width: 6px; height: 6px; border-radius: 50%; background: #F59E0B; animation: pulse-dot 0.8s ease-in-out infinite; }
}
.grammar-indicator { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 14px; cursor: pointer; font-size: 11px; color: #92400E; user-select: none; transition: all 0.2s; margin-top: 4px;
  &:hover { background: #FEF3C7; } &.expanded { border-radius: 14px 14px 0 0; border-bottom: none; }
  .gi-icon { font-size: 12px; } .gi-text { flex: 1; }
  .gi-count { background: #F59E0B; color: #fff; border-radius: 10px; padding: 0 6px; font-size: 10px; font-weight: 600; min-width: 16px; text-align: center; }
  .gi-arrow { font-size: 10px; transition: transform 0.2s; color: #B45309; }
  &.expanded .gi-arrow { transform: rotate(180deg); }
}
.grammar-correction-card { background: #FFFBEB; border: 1px solid #FDE68A; border-top: none; border-radius: 0 0 14px 14px; padding: 8px 12px 10px; margin-top: -1px; animation: gcSlideIn 0.2s ease; }
@keyframes gcSlideIn { from { opacity: 0; max-height: 0; } to { opacity: 1; max-height: 300px; } }
.gc-corrected { display: flex; gap: 6px; padding: 6px 0; margin-bottom: 4px; border-bottom: 1px dashed #FDE68A;
  .gc-label { font-size: 11px; color: #92400E; font-weight: 600; flex-shrink: 0; }
  .gc-corrected-text { font-size: 12px; color: #4A4A5A; line-height: 1.5; }
}
.gc-error-item { display: flex; align-items: center; gap: 6px; padding: 5px 0; flex-wrap: wrap; & + & { border-top: 1px solid #FEF3C7; }
  .gc-error-original { font-size: 11px; color: #DC2626; text-decoration: line-through; background: #FEE2E2; padding: 1px 5px; border-radius: 4px; }
  .gc-error-arrow { font-size: 10px; color: #999; }
  .gc-error-correction { font-size: 11px; color: #059669; font-weight: 600; background: #D1FAE5; padding: 1px 5px; border-radius: 4px; }
  .gc-error-type { font-size: 10px; color: #fff; padding: 1px 5px; border-radius: 8px; font-weight: 500; flex-shrink: 0; }
  .gc-error-explain { font-size: 11px; color: #999; width: 100%; margin-top: 2px; padding-left: 2px; }
}

.call-actions { display: flex; align-items: center; justify-content: center; gap: 24px; padding: 16px 20px 36px; flex-shrink: 0; }
.pause-btn { width: 52px; height: 52px; border-radius: 50%; border: none; background: #F0E8FF; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.25s;
  .pause-icon { font-size: 20px; } &:hover { background: #E0D0FF; transform: scale(1.05); } &:active { transform: scale(0.95); }
}
.pause-label { font-size: 11px; color: #bbb; margin: 0; text-align: center; }
.hangup-btn { width: 52px; height: 52px; border-radius: 50%; border: none; background: linear-gradient(135deg, #FF6B8A, #FF8E9E); color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 16px rgba(255,107,138,0.3); transition: all 0.25s;
  .hangup-icon { font-size: 22px; } &:hover { transform: scale(1.08); box-shadow: 0 6px 24px rgba(255,107,138,0.4); } &:active { transform: scale(0.95); }
}
.hangup-label { font-size: 11px; color: #bbb; margin: 0; text-align: center; }

.report-screen { min-height: calc(100vh - 56px); background: linear-gradient(180deg, #FFF5F5 0%, #F8F0FF 30%, #FFF9F0 100%); padding: 24px 24px 32px; max-width: 1400px; margin: 0 auto; }
.report-header { text-align: center; margin-bottom: 16px; .report-mascot { font-size: 40px; margin-bottom: 4px; } h2 { font-size: 22px; font-weight: 700; color: #3D3D5C; margin: 0; } .report-role { font-size: 13px; color: #999; margin-top: 4px; } }
.report-top { display: flex; align-items: center; gap: 24px; margin-bottom: 20px; padding: 20px 28px; background: #fff; border-radius: 20px; box-shadow: 0 2px 16px rgba(0,0,0,0.04); }
.overall-area { display: flex; align-items: center; gap: 28px; flex: 1; }
.overall-circle { width: 110px; height: 110px; border-radius: 50%; background: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.06); display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;
  .overall-num { font-size: 38px; font-weight: 800; color: #3D3D5C; line-height: 1; } .overall-unit { font-size: 12px; color: #999; margin-top: 2px; } .overall-level { font-size: 12px; font-weight: 600; margin-top: 2px; color: #FF6B8A; }
}
.methodology-card { flex: 1; padding: 14px 18px; background: #F8F0FF; border-radius: 14px;
  .methodology-title { font-size: 13px; font-weight: 600; color: #7C6FF7; margin-bottom: 6px; }
  .methodology-text { font-size: 12px; color: #666; line-height: 1.7; white-space: pre-wrap; font-family: inherit; margin: 0; }
}
.report-main { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.report-bottom { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.report-card { background: #fff; border-radius: 20px; padding: 20px 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.04); &--full { grid-column: 1 / -1; margin-bottom: 16px; } }
.card-title { font-size: 16px; font-weight: 700; color: #3D3D5C; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; .card-icon { font-size: 18px; } }
.dimension-list { display: flex; flex-direction: column; gap: 10px; }
.dimension-item { .dim-header { display: flex; justify-content: space-between; margin-bottom: 4px; .dim-label { font-size: 13px; color: #666; } .dim-score { font-size: 14px; font-weight: 700; } }
  .dim-bar-bg { height: 7px; border-radius: 4px; background: #F0E8FF; overflow: hidden; } .dim-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
}
.error-section { margin-top: 16px; .error-title { font-size: 13px; font-weight: 600; color: #3D3D5C; margin-bottom: 8px; } }
.error-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: rgba(255,107,138,0.04); border-radius: 8px; margin-bottom: 6px; .error-actual { font-size: 12px; color: #FF6B8A; font-family: monospace; } .error-tip-text { font-size: 11px; color: #999; flex: 1; } }
.text-dim-cards { display: flex; flex-direction: column; gap: 14px; }
.text-dim-card { padding: 14px; background: #FAFAFF; border-radius: 14px; border: 1px solid #F0E8FF;
  .tdc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; } .tdc-label { font-size: 14px; font-weight: 600; color: #3D3D5C; } .tdc-score { font-size: 22px; font-weight: 800; }
  .tdc-feedback { font-size: 12px; color: #666; line-height: 1.5; margin-bottom: 6px; } .tdc-tags { display: flex; flex-direction: column; gap: 3px; } .tdc-tag { font-size: 11px; &.good { color: #5AD8A6; } &.improve { color: #FF6B8A; } }
}
.utterance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 10px; }
.utterance-item { border: 1px solid #F0E8FF; border-radius: 12px; overflow: hidden; &.expanded { grid-column: 1 / -1; } }
.utterance-header { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; transition: background 0.2s; &:hover { background: #FAFAFF; }
  .utterance-num { font-size: 11px; font-weight: 600; color: #7C6FF7; background: rgba(124,111,247,0.08); padding: 2px 8px; border-radius: 8px; flex-shrink: 0; }
  .utterance-text-preview { font-size: 13px; color: #666; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .utterance-score { font-size: 15px; font-weight: 700; flex-shrink: 0; } .utterance-arrow { font-size: 10px; color: #ccc; flex-shrink: 0; transition: transform 0.25s; &.expanded { transform: rotate(90deg); } }
}
.utterance-detail-wrap { border-top: 1px solid #F0E8FF; padding: 0 16px 8px; }
.transcript-list { display: flex; flex-direction: column; gap: 10px; max-height: 300px; overflow-y: auto; }
.transcript-msg { display: flex; flex-direction: column; max-width: 90%; &.user { align-self: flex-end; } &.ai { align-self: flex-start; } &.grammar { align-self: flex-start; }
  .transcript-role { font-size: 10px; color: #999; margin-bottom: 2px; padding: 0 4px; } &.user .transcript-role { text-align: right; }
  .transcript-bubble { padding: 8px 12px; border-radius: 12px; font-size: 12px; line-height: 1.5; color: #4A4A5A; }
  &.user .transcript-bubble { background: #F0F0FF; border-bottom-right-radius: 4px; } &.ai .transcript-bubble { background: #FFF0F3; border-bottom-left-radius: 4px; }
}
.transcript-grammar { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 10px 12px; font-size: 11px;
  .tg-corrected { display: flex; gap: 4px; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px dashed #FDE68A; .tg-label { color: #92400E; font-weight: 600; flex-shrink: 0; } .tg-corrected-text { color: #4A4A5A; } }
  .tg-error { display: flex; align-items: center; gap: 4px; padding: 3px 0; flex-wrap: wrap; font-size: 11px; color: #666;
    .tg-error-original { color: #DC2626; text-decoration: line-through; background: #FEE2E2; padding: 0 4px; border-radius: 3px; }
    .tg-error-correction { color: #059669; font-weight: 600; background: #D1FAE5; padding: 0 4px; border-radius: 3px; }
    .tg-error-type { font-size: 10px; color: #fff; padding: 0 5px; border-radius: 8px; } .tg-error-explain { width: 100%; color: #999; font-size: 10px; margin-top: 1px; }
  }
}
.suggestions-content { p { font-size: 13px; color: #666; line-height: 1.7; margin: 0; } }
.fluency-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 8px;
  &.grade-优秀 { background: #E8F8F0; color: #3EC790; } &.grade-良好 { background: #E8F0FF; color: #5B8DEF; }
  &.grade-中等 { background: #FFF8E8; color: #F0A030; } &.grade-初级 { background: #FFF0E8; color: #F08040; } &.grade-入门 { background: #FFE8E8; color: #E05050; }
}
.fluency-overall { font-size: 13px; color: #888; margin-left: auto; }
.fluency-rounds { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.fluency-round-card { background: #FAFBFC; border: 1px solid #EBEEF5; border-radius: 10px; padding: 12px 16px; &.best-round { border-color: #F6BD16; background: #FFFDF5; } }
.fr-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; } .fr-label { font-size: 13px; font-weight: 600; color: #555; } .fr-best { font-size: 11px; color: #F0A030; } .fr-total { font-size: 14px; font-weight: 700; color: #4A4A5A; margin-left: auto; }
.fr-text { font-size: 12px; color: #999; margin-bottom: 10px; font-style: italic; line-height: 1.5; }
.fr-dims { display: flex; gap: 12px; flex-wrap: wrap; }
.fr-dim { display: flex; flex-direction: column; align-items: center; background: #fff; border-radius: 8px; padding: 8px 12px; min-width: 70px; border: 1px solid #F0F0F0; }
.fd-label { font-size: 11px; color: #999; margin-bottom: 2px; } .fd-value { font-size: 15px; font-weight: 700; } .fd-detail { font-size: 10px; color: #bbb; margin-top: 2px; }
.fluency-suggestions { margin-top: 14px; padding: 12px; background: #F0F8FF; border-radius: 8px; font-size: 13px; color: #5B8DEF; line-height: 1.6; }
.report-loading { text-align: center; padding: 80px 20px;
  .loading-spinner { width: 40px; height: 40px; border: 3px solid #F0E8FF; border-top-color: #FF6B8A; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; } p { color: #999; font-size: 14px; }
}
@keyframes spin { to { transform: rotate(360deg); } }
.report-actions { display: flex; gap: 12px; justify-content: center; padding-top: 8px;
  .retry-btn, .back-btn { display: flex; align-items: center; gap: 6px; padding: 10px 22px; border-radius: 22px; border: none; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; span { font-size: 16px; } }
  .retry-btn { background: linear-gradient(135deg, #FF6B8A, #FF8E9E); color: #fff; box-shadow: 0 4px 12px rgba(255,107,138,0.3); &:hover { transform: translateY(-2px); } }
  .back-btn { background: #fff; color: #666; box-shadow: 0 2px 8px rgba(0,0,0,0.06); &:hover { transform: translateY(-2px); } }
}
</style>