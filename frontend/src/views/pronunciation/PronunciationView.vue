<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import DimensionBars from '@/components/common/DimensionBars.vue'
import { scorePronunciation, getContentList, getRecordList } from '@/api/pronunciation'

// 后端内容库
const contentList = ref([])
const contentLoading = ref(false)

// 状态
const mode = ref('word')
const difficulty = ref('A1')
const contentIndex = ref(0)
const recorderRef = ref(null)
const hasScored = ref(false)
const scoreResult = ref(null)
const isScoring = ref(false)
const scoreError = ref('')
const showDetail = ref(false)
const detailTab = ref('phoneme')
const recordingBlob = ref(null)
const recordingUrl = ref('')
const referenceUrl = ref('')

// 历史记录
const showHistory = ref(false)
const historyRecords = ref([])
const historyLoading = ref(false)

// 自定义播放器状态
const userAudioRef = ref(null)
const refAudioRef = ref(null)
const userPlaying = ref(false)
const refPlaying = ref(false)
const userCurrentTime = ref(0)
const refCurrentTime = ref(0)
const userDuration = ref(0)
const refDuration = ref(0)

const userTime = computed(() => formatTime(userCurrentTime.value))
const refTime = computed(() => formatTime(refCurrentTime.value))

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function toggleUserPlay() {
  const a = userAudioRef.value
  if (!a) return
  a.paused ? a.play() : a.pause()
}

function toggleRefPlay() {
  const a = refAudioRef.value
  if (!a) return
  a.paused ? a.play() : a.pause()
}

function onUserTimeUpdate() {
  const a = userAudioRef.value
  if (a) { userCurrentTime.value = a.currentTime; userDuration.value = a.duration || 0 }
}

function onRefTimeUpdate() {
  const a = refAudioRef.value
  if (a) { refCurrentTime.value = a.currentTime; refDuration.value = a.duration || 0 }
}

const waveTick = ref(0)
let waveRaf = null

function waveLoop() {
  waveTick.value++
  waveRaf = requestAnimationFrame(waveLoop)
}

onMounted(() => {
  waveRaf = requestAnimationFrame(waveLoop)
  loadContent()
})

onUnmounted(() => {
  if (waveRaf) cancelAnimationFrame(waveRaf)
})

function waveStyle(side, i) {
  const playing = side === 'user' ? userPlaying.value : refPlaying.value
  if (!playing) return { height: '3px' }
  const t = waveTick.value
  const h = 3 + Math.sin(t / 12 + i * 0.5) * 8 + Math.sin(t / 7 + i) * 4
  return { height: `${Math.max(2, Math.abs(h))}px` }
}

const difficultyOptions = ['A1', 'A2', 'B1', 'B2']

// 加载跟读内容
async function loadContent() {
  contentLoading.value = true
  try {
    const list = await getContentList(mode.value, difficulty.value)
    contentList.value = list || []
    contentIndex.value = 0
  } catch {
    contentList.value = []
  } finally {
    contentLoading.value = false
  }
}

// 加载历史记录
async function loadHistory() {
  historyLoading.value = true
  try {
    historyRecords.value = await getRecordList(20) || []
  } catch {
    historyRecords.value = []
  } finally {
    historyLoading.value = false
  }
}

function openHistory() {
  showHistory.value = true
  loadHistory()
}

const currentItem = computed(() => {
  if (contentList.value.length === 0) return null
  const item = contentList.value[contentIndex.value % contentList.value.length]
  return item
})

const currentText = computed(() => {
  if (!currentItem.value) return ''
  return currentItem.value.content_text || ''
})

const isWordMode = computed(() => mode.value === 'word')

const scoreLevel = computed(() => {
  const s = scoreResult.value?.overall || 0
  if (s >= 80) return { label: '优秀', type: 'success' }
  if (s >= 60) return { label: '良好', type: 'warning' }
  return { label: '需加强', type: 'danger' }
})

function switchMode(newMode) {
  mode.value = newMode
  resetState()
  loadContent()
}

function handleDifficultyChange() {
  resetState()
  loadContent()
}

function resetState() {
  contentIndex.value = 0
  hasScored.value = false
  scoreResult.value = null
  scoreError.value = ''
  showDetail.value = false
  detailTab.value = 'phoneme'
  recorderRef.value?.reset()
}

async function handleRecordComplete({ blob, elapsed }) {
  isScoring.value = true
  scoreError.value = ''

  // 保存用户录音用于回放
  recordingBlob.value = blob
  if (recordingUrl.value) URL.revokeObjectURL(recordingUrl.value)
  recordingUrl.value = URL.createObjectURL(blob)

  try {
    // 并行：评分 + 获取标准音
    const [result] = await Promise.all([
      scorePronunciation(blob, currentText.value, mode.value),
      fetchReferenceAudio(),
    ])
    scoreResult.value = result
    hasScored.value = true
    recorderRef.value?.setScored()
  } catch (e) {
    scoreError.value = '评分失败，请检查网络连接后重试'
    ElMessage.error('评分请求失败')
  } finally {
    isScoring.value = false
  }
}

async function fetchReferenceAudio() {
  try {
    const form = new FormData()
    form.append('text', currentText.value)
    form.append('voice', 'en-US-JennyNeural')
    const response = await fetch('/api/pronunciation/reference-audio', {
      method: 'POST',
      body: form,
    })
    if (response.ok) {
      const blob = await response.blob()
      if (referenceUrl.value) URL.revokeObjectURL(referenceUrl.value)
      referenceUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) {
    console.warn('获取标准音失败:', e)
  }
}

function nextContent() {
  contentIndex.value++
  hasScored.value = false
  scoreResult.value = null
  scoreError.value = ''
  showDetail.value = false
  if (recordingUrl.value) { URL.revokeObjectURL(recordingUrl.value); recordingUrl.value = '' }
  if (referenceUrl.value) { URL.revokeObjectURL(referenceUrl.value); referenceUrl.value = '' }
  recorderRef.value?.reset()
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

const levelTable = [
  { range: '80 - 100', level: '优秀', desc: '发音近似母语者，音素清晰准确' },
  { range: '60 - 79', level: '良好', desc: '基本正确，个别音素可改进' },
  { range: '40 - 59', level: '一般', desc: '部分音素偏差较大，需针对性练习' },
  { range: '0 - 39', level: '需练习', desc: '多数音素与标准发音差距明显，建议从基础音标练起' },
]

function getCharScoreBg(score) {
  if (score >= 80) return 'rgba(103,194,58,0.15)'
  if (score >= 60) return 'rgba(230,162,60,0.15)'
  if (score >= 40) return 'rgba(230,162,60,0.08)'
  return 'rgba(245,108,108,0.12)'
}

function getCharScoreBorder(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  if (score >= 40) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

// --- 重音分析辅助 ---
const stressCount = computed(() => {
  return (scoreResult.value?.stress_viz?.is_stressed || []).filter(Boolean).length
})

const stressChars = computed(() => {
  const viz = scoreResult.value?.stress_viz
  if (!viz?.chars) return ''
  return viz.chars.filter((_, i) => viz.is_stressed[i]).join(', ') || '无'
})

function stressCVExplain(cv) {
  if (cv == null) return ''
  if (cv < 0.05) return '→ 能量过于平坦，像机器人发音'
  if (cv < 0.15) return '→ 有轻微起伏，重音变化不够明显'
  if (cv < 0.40) return '→ 能量起伏自然，有重音层次感'
  if (cv < 0.80) return '→ 重音变化明显，表达有力'
  return '→ 能量起伏过大，发音可能不稳定'
}

function durCVExplain(cv) {
  if (cv == null) return ''
  if (cv < 0.05) return '→ 时长过于均匀，缺少节奏变化'
  if (cv < 0.30) return '→ 时长分布适中'
  return '→ 时长有节奏变化，重读音节明显更长'
}

// --- 语调分析辅助 ---
const sentenceTypeLabel = computed(() => {
  const t = scoreResult.value?.intonation_viz?.sentence_type
  if (t === 'question') return '疑问句'
  if (t === 'exclamation') return '感叹句'
  return '陈述句'
})

const expectedIntonation = computed(() => {
  const t = scoreResult.value?.intonation_viz?.sentence_type
  if (t === 'question') return '句尾上扬 ↗'
  if (t === 'exclamation') return '大幅起伏 ↕'
  return '自然下降 ↘'
})

function rangeExplain(st) {
  if (st == null) return ''
  if (st < 1.5) return '→ 过于平坦，像机器人'
  if (st < 4) return '→ 音高变化适中'
  if (st < 8) return '→ 音高变化丰富，语调生动'
  return '→ 音高范围很宽，表达富有感染力'
}

// --- 连读分析辅助 ---
const linkingPairs = computed(() => scoreResult.value?.linking_viz?.pairs || [])
const linkablePairs = computed(() => linkingPairs.value.filter(p => p.linkable))
const linkedPairs = computed(() => linkablePairs.value.filter(p => p.gap_ms <= 30))

function gapExplain(ms) {
  if (ms == null) return ''
  if (ms <= 30) return '→ 几乎无缝，连读到位'
  if (ms <= 80) return '→ 轻微间隙，连读尚可'
  if (ms <= 150) return '→ 间隙明显，有蹦词感'
  return '→ 断开明显，逐词蹦读'
}

function phonemeLabel(ph) {
  if (!ph) return ''
  const p = ph.replace(/[012]/, '')
  return `/ ${p.toLowerCase()} /`
}

// --- 节奏感分析辅助 ---
function rhythmCVExplain(cv) {
  if (cv == null) return ''
  if (cv < 0.15) return '→ 过于均匀，像机器人发音'
  if (cv < 0.30) return '→ 节奏自然流畅，符合英语轻重节拍'
  if (cv < 0.50) return '→ 有些波动，基本可接受'
  if (cv < 0.80) return '→ 节奏不够稳定，时快时慢'
  return '→ 节奏非常不均匀，影响可懂度'
}

const pauseSlots = computed(() => {
  const viz = scoreResult.value?.rhythm_viz
  if (!viz?.is_pause) return []
  return viz.is_pause.map((pause, i) => pause ? { char: viz.chars[i], dur: viz.durations_ms[i] } : null).filter(Boolean)
})

const rhythmSummary = computed(() => {
  const viz = scoreResult.value?.rhythm_viz
  if (!viz) return '暂无节奏数据'
  const cv = viz.cv
  const pause = viz.pause_count
  let msg = `平均音素时长 ${viz.mean_ms}ms，变异系数 ${cv} —— `
  if (cv < 0.15) msg += '过于均匀，像机器人发音'
  else if (cv < 0.30) msg += '节奏自然流畅，符合英语轻重节拍'
  else if (cv < 0.50) msg += '节奏有些波动，基本可接受'
  else if (cv < 0.80) msg += '节奏不够稳定，时快时慢较明显'
  else msg += '节奏非常不均匀，忽快忽慢'
  if (pause > 0) msg += `；检测到 ${pause} 处异常卡顿`
  return msg
})
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">AI 发音评测</h2>

    <!-- 模式切换 -->
    <div class="control-bar">
      <el-radio-group v-model="mode" @change="switchMode" size="large">
        <el-radio-button value="word">单词模式</el-radio-button>
        <el-radio-button value="sentence">句子模式</el-radio-button>
      </el-radio-group>

      <div class="control-right">
        <span class="control-label">难度筛选：</span>
        <el-select
          v-model="difficulty"
          @change="handleDifficultyChange"
          style="width: 100px"
          size="small"
        >
          <el-option v-for="d in difficultyOptions" :key="d" :label="d" :value="d" />
        </el-select>
        <el-button size="small" @click="openHistory">
          <el-icon><Clock /></el-icon> 历史记录
        </el-button>
      </div>
    </div>

    <!-- 跟读内容卡片 -->
    <div class="content-display" v-if="currentItem">
      <div class="content-main">
        <span v-if="isWordMode" class="word-text">{{ currentItem.content_text }}</span>
        <span v-else class="sentence-text">{{ currentItem.content_text }}</span>
      </div>
      <div v-if="isWordMode && currentItem.phonetic_ipa" class="content-ipa">{{ currentItem.phonetic_ipa }}</div>
      <div v-if="currentItem.title" class="content-chinese">{{ currentItem.title }}</div>
      <el-button size="small" text type="primary" class="play-btn" @click="fetchReferenceAudio">
        <el-icon><VideoPlay /></el-icon> 播放标准音
      </el-button>
    </div>
    <div v-else-if="contentLoading" class="content-display">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <p style="color: var(--color-text-secondary); margin-top: 8px;">加载跟读内容...</p>
    </div>
    <div v-else class="content-display">
      <p style="color: var(--color-text-disabled);">暂无{{ difficulty }}级{{ mode === 'word' ? '单词' : '句子' }}内容</p>
    </div>

    <!-- 录音区域 -->
    <div class="record-section" v-if="!hasScored && !isScoring">
      <VoiceRecorder
        ref="recorderRef"
        :prep-time="3"
        :max-duration="isWordMode ? 10 : 30"
        :disabled="isScoring"
        @complete="handleRecordComplete"
      />
    </div>

    <!-- 评分中 -->
    <div class="record-section" v-if="isScoring">
      <el-icon class="is-loading" :size="36"><Loading /></el-icon>
      <p style="color: var(--color-text-secondary); margin-top: 8px;">正在分析发音...</p>
    </div>

    <!-- 评分错误 -->
    <el-alert
      v-if="scoreError"
      type="error"
      :title="scoreError"
      show-icon
      closable
      @close="scoreError = ''"
      style="margin-bottom: var(--spacing-lg);"
    />

    <!-- 评分结果 -->
    <div v-if="hasScored && scoreResult" class="score-section">
      <div class="score-divider">
        <span>评分结果</span>
      </div>

      <!-- 综合分 -->
      <div class="overall-score" :style="{ color: getScoreColor(scoreResult.overall) }">
        <span class="overall-number">{{ scoreResult.overall }}</span>
        <span class="overall-unit">分</span>
        <el-tag
          :type="scoreResult.overall >= 80 ? 'success' : scoreResult.overall >= 60 ? 'warning' : 'danger'"
          size="small"
        >
          {{ scoreResult.overall >= 80 ? '优秀' : scoreResult.overall >= 60 ? '良好' : '需加强' }}
        </el-tag>
      </div>

      <!-- 五维评分 -->
      <DimensionBars :dimensions="scoreResult.dimensions" />

      <!-- 查看详情按钮 -->
      <div class="detail-trigger">
        <el-button type="primary" text @click="showDetail = true">
          <el-icon><View /></el-icon> 查看详细评分
        </el-button>
      </div>

      <!-- 错误音素 -->
      <div class="error-section">
        <h4>错误音素定位</h4>
        <div v-for="err in scoreResult.errors" :key="err.phoneme" class="error-item">
          <div class="error-phoneme">
            <el-tag type="danger" size="small">{{ err.phoneme }}</el-tag>
            <span class="error-actual">{{ err.actual }}</span>
          </div>
          <p class="error-tip">
            <el-icon><InfoFilled /></el-icon>
            {{ err.tip }}
          </p>
        </div>
      </div>

      <!-- 下一题 -->
      <el-button type="primary" @click="nextContent" style="width: 100%;">
        下一个
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- ============================================================ -->
    <!-- 详细评分弹窗 -->
    <!-- ============================================================ -->

    <!-- ============================================================ -->
    <!-- 历史记录弹窗 -->
    <!-- ============================================================ -->
    <el-dialog
      v-model="showHistory"
      title="评测历史记录"
      width="700px"
      destroy-on-close
    >
      <el-table
        v-loading="historyLoading"
        :data="historyRecords"
        size="small"
        stripe
        empty-text="暂无评测记录"
      >
        <el-table-column label="内容" min-width="160">
          <template #default="{ row }">
            <span>{{ row.content_text || row.content_title || '自由跟读' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mode" label="模式" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.mode === 'word' ? 'primary' : 'success'">
              {{ row.mode === 'word' ? '单词' : '句子' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="综合分" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.overall_score >= 80 ? 'var(--color-success)' : row.overall_score >= 60 ? 'var(--color-warning)' : 'var(--color-danger)', fontWeight: 700 }">
              {{ row.overall_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="音素分" width="90" align="center">
          <template #default="{ row }">
            <span>{{ row.phoneme_score ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">
            <span style="font-size: 12px; color: var(--color-text-secondary);">
              {{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    <el-dialog
      v-model="showDetail"
      title="发音详细评分报告"
      width="1100px"
      :close-on-click-modal="false"
      destroy-on-close
      top="3vh"
      class="score-dialog"
    >
      <template #header>
        <div class="dialog-header">
          <span class="dialog-title">发音详细评分报告</span>
          <el-tag :type="scoreLevel.type" size="small">{{ scoreLevel.label }}</el-tag>
        </div>
      </template>

      <!-- 综合分数 -->
      <div class="detail-overview">
        <div class="detail-score-ring" :style="{ color: getScoreColor(scoreResult.overall) }">
          <span class="ring-number">{{ scoreResult.overall }}</span>
          <span class="ring-unit">/100</span>
        </div>
        <div class="detail-overview-text">
          <p class="overview-text-item">评测文本：<strong>{{ currentText }}</strong></p>
          <p class="overview-text-item">评分音素：<strong>{{ scoreResult.char_scores?.length || 0 }}</strong> 个</p>
          <p class="overview-text-item">问题音素：<strong>{{ scoreResult.errors?.length || 0 }}</strong> 个</p>
        </div>
      </div>

      <!-- 维度分析说明 -->
      <div v-if="scoreResult.analysis_detail" class="detail-insights">
        <div class="insight-item">
          <el-icon :size="16"><MagicStick /></el-icon>
          <div>
            <strong>重音位置：</strong>
            <span>{{ scoreResult.analysis_detail.stress }}</span>
          </div>
        </div>
        <div class="insight-item">
          <el-icon :size="16"><MagicStick /></el-icon>
          <div>
            <strong>语调曲线：</strong>
            <span>{{ scoreResult.analysis_detail.intonation }}</span>
          </div>
        </div>
      </div>

      <!-- 对比播放器 -->
      <div class="compare-players">
        <!-- 用户录音 -->
        <div class="player-card user-card">
          <div class="player-header">
            <span class="player-label">
              <span class="player-dot-user"></span> 你的录音
            </span>
            <span class="player-time">{{ userTime }}</span>
          </div>
          <div class="player-controls">
            <button class="player-play-btn" @click="toggleUserPlay">
              <span v-if="!userPlaying" class="play-icon">▶</span>
              <span v-else class="play-icon">⏸</span>
            </button>
            <div class="player-wave">
              <span
                v-for="i in 16"
                :key="'uw'+i"
                class="wave-bar"
                :style="waveStyle('user', i)"
              />
            </div>
          </div>
        </div>

        <div class="vs-badge">VS</div>

        <!-- 标准发音 -->
        <div class="player-card ref-card">
          <div class="player-header">
            <span class="player-label">
              <span class="player-dot-ref"></span> 标准发音
            </span>
            <span class="player-time">{{ refTime }}</span>
          </div>
          <div class="player-controls">
            <button class="player-play-btn" @click="toggleRefPlay">
              <span v-if="!refPlaying" class="play-icon">▶</span>
              <span v-else class="play-icon">⏸</span>
            </button>
            <div class="player-wave">
              <span
                v-for="i in 16"
                :key="'rw'+i"
                class="wave-bar"
                :style="waveStyle('ref', i)"
              />
            </div>
          </div>
        </div>
      </div>

      <el-divider />

      <!-- Tab: 逐音素评分 / 可视化分析 / 评分说明 -->
      <el-tabs v-model="detailTab">
        <el-tab-pane label="逐音素评分" name="phoneme">
          <!-- 文本高亮条 -->
          <div class="phoneme-strip">
            <div
              v-for="(cs, i) in scoreResult.char_scores"
              :key="i"
              class="phoneme-chip"
              :style="{
                background: getCharScoreBg(cs.score),
                borderColor: getCharScoreBorder(cs.score),
              }"
            >
              <span class="chip-char">{{ cs.char }}</span>
              <span class="chip-score">{{ cs.score }}</span>
            </div>
            <p v-if="!scoreResult.char_scores?.length" class="text-muted">暂无逐音素数据</p>
          </div>

          <!-- 音素评分表格 -->
          <el-table
            v-if="scoreResult.char_scores?.length"
            :data="scoreResult.char_scores"
            size="small"
            stripe
            max-height="300"
            style="margin-top: 16px;"
          >
            <el-table-column prop="char" label="音素" width="80" align="center" />
            <el-table-column prop="score" label="GOP 得分" width="120" align="center">
              <template #default="{ row }">
                <span :style="{ color: getScoreColor(row.score), fontWeight: 600 }">
                  {{ row.score }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="duration_ms" label="时长(ms)" width="100" align="center" />
            <el-table-column prop="level" label="评级" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.score >= 80 ? 'success' : row.score >= 60 ? 'warning' : 'danger'"
                  size="small"
                >
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" min-width="120">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.min(row.score, 100)"
                  :color="row.score >= 80 ? 'var(--color-success)' : row.score >= 60 ? 'var(--color-warning)' : 'var(--color-danger)'"
                  :stroke-width="8"
                  :show-text="false"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ===== 重音位置分析 ===== -->
        <el-tab-pane label="重音位置分析" name="stress">
          <div class="viz-section">
            <!-- 分析结论 -->
            <div class="model-insight">
              <el-icon :size="16"><InfoFilled /></el-icon>
              <span>{{ scoreResult.analysis_detail?.stress || '无分析数据' }}</span>
            </div>

            <!-- 能量柱状图 -->
            <h4 class="viz-title">音素能量分布</h4>
            <div v-if="scoreResult.stress_viz?.chars?.length" class="stress-chart">
              <div
                v-for="(ch, i) in scoreResult.stress_viz.chars"
                :key="'s'+i"
                class="stress-bar-col"
              >
                <div class="stress-bar-fill-wrap">
                  <div
                    class="stress-bar-fill"
                    :style="{
                      height: (scoreResult.stress_viz.energies[i] * 100) + '%',
                      background: scoreResult.stress_viz.is_stressed[i]
                        ? 'var(--color-primary)'
                        : 'var(--color-border)',
                    }"
                  />
                </div>
                <span
                  class="stress-bar-label"
                  :style="{
                    color: scoreResult.stress_viz.is_stressed[i]
                      ? 'var(--color-primary)'
                      : 'var(--color-text-secondary)',
                    fontWeight: scoreResult.stress_viz.is_stressed[i] ? 700 : 400,
                  }"
                >{{ ch }}</span>
              </div>
            </div>
            <div class="viz-legend">
              <span class="legend-dot" style="background:var(--color-primary)"></span> 重读音节
              <span class="legend-dot" style="background:var(--color-border)"></span> 非重读音节
            </div>

            <!-- 模型输出数据 -->
            <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
            <div class="model-data-grid">
              <div class="model-data-item">
                <span class="data-label">能量变异系数 (CV)</span>
                <span class="data-value">{{ scoreResult.stress_viz?.energy_cv ?? '-' }}</span>
                <span class="data-explain">{{ stressCVExplain(scoreResult.stress_viz?.energy_cv) }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">时长变异系数 (CV)</span>
                <span class="data-value">{{ scoreResult.stress_viz?.dur_cv ?? '-' }}</span>
                <span class="data-explain">{{ durCVExplain(scoreResult.stress_viz?.dur_cv) }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">检测到重读音节</span>
                <span class="data-value">{{ stressCount }} 个</span>
                <span class="data-explain">{{ stressChars }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">归一化能量序列</span>
                <span class="data-value" style="font-size:11px;font-family:monospace;">[{{ (scoreResult.stress_viz?.energies || []).map(v => v.toFixed(2)).join(', ') }}]</span>
                <span class="data-explain">0~1 归一化，值越大能量越强</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ===== 语调曲线分析 ===== -->
        <el-tab-pane label="语调曲线分析" name="intonation">
          <div class="viz-section">
            <!-- 分析结论 -->
            <div class="model-insight">
              <el-icon :size="16"><InfoFilled /></el-icon>
              <span>{{ scoreResult.analysis_detail?.intonation || '无分析数据' }}</span>
            </div>

            <!-- 句类标签 + 方向 -->
            <h4 class="viz-title">
              F0 基频曲线
              <el-tag size="small" :type="scoreResult.intonation_viz?.sentence_type === 'question' ? 'warning' : 'primary'">
                {{ scoreResult.intonation_viz?.sentence_type === 'question' ? '疑问句' : scoreResult.intonation_viz?.sentence_type === 'exclamation' ? '感叹句' : '陈述句' }}
              </el-tag>
              <span class="intonation-expect">
                预期: {{ expectedIntonation }}
              </span>
            </h4>

            <div v-if="scoreResult.intonation_viz?.f0_points?.length" class="intonation-chart">
              <div class="intonation-direction">
                <span class="direction-arrow" :style="{
                  transform: scoreResult.intonation_viz.slope_st_per_sec > 0.2 ? 'rotate(-45deg)' : scoreResult.intonation_viz.slope_st_per_sec < -0.2 ? 'rotate(45deg)' : 'rotate(0deg)',
                }">➤</span>
                <span class="direction-label">{{ scoreResult.intonation_viz.direction }}</span>
              </div>
              <svg
                v-if="scoreResult.intonation_viz.f0_points.length > 1"
                class="f0-curve-svg"
                :viewBox="`0 0 ${scoreResult.intonation_viz.f0_points.length * 12} 100`"
              >
                <polyline
                  :points="scoreResult.intonation_viz.f0_points.map((p, i) => {
                    const hzMin = Math.min(...scoreResult.intonation_viz.f0_points.map(x => x.hz))
                    const hzMax = Math.max(...scoreResult.intonation_viz.f0_points.map(x => x.hz))
                    const range = hzMax - hzMin || 1
                    const y = 95 - ((p.hz - hzMin) / range) * 80
                    return `${i * 12 + 6},${y}`
                  }).join(' ')"
                  fill="none"
                  stroke="var(--color-primary)"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <p v-else class="text-muted">基频数据不足，无法绘制曲线</p>

            <!-- 模型输出数据 -->
            <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
            <div class="model-data-grid">
              <div class="model-data-item">
                <span class="data-label">基频斜率 (F0 Slope)</span>
                <span class="data-value">{{ scoreResult.intonation_viz?.slope_st_per_sec ?? '-' }} st/s</span>
                <span class="data-explain">正值=升调，负值=降调，接近0=平调</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">音高范围 (F0 Range)</span>
                <span class="data-value">{{ scoreResult.intonation_viz?.range_st ?? '-' }} 半音</span>
                <span class="data-explain">{{ rangeExplain(scoreResult.intonation_viz?.range_st) }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">基频采样点数</span>
                <span class="data-value">{{ (scoreResult.intonation_viz?.f0_points || []).length }} 帧</span>
                <span class="data-explain">PYIN 算法提取的有声音帧</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">句类判断</span>
                <span class="data-value">{{ sentenceTypeLabel }}</span>
                <span class="data-explain">预期语调: {{ expectedIntonation }}</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ===== 连读表现分析 ===== -->
        <el-tab-pane label="连读表现" name="linking">
          <div class="viz-section">
            <!-- 分析结论 -->
            <div class="model-insight">
              <el-icon :size="16"><InfoFilled /></el-icon>
              <span>{{ scoreResult.analysis_detail?.linking || '无分析数据' }}</span>
            </div>

            <!-- 词间连读概览 -->
            <h4 class="viz-title">
              词间连读分析
              <el-tag size="small" :type="linkablePairs.length > 0 ? 'warning' : 'info'">
                {{ linkablePairs.length }} 处可连读
              </el-tag>
              <el-tag
                v-if="linkablePairs.length > 0"
                size="small"
                :type="linkedPairs.length >= linkablePairs.length * 0.7 ? 'success' : 'warning'"
              >
                {{ linkedPairs.length }} 处已连上
              </el-tag>
            </h4>

            <!-- 词对分析表格 -->
            <el-table
              v-if="linkingPairs.length > 0"
              :data="linkingPairs"
              size="small"
              stripe
              max-height="280"
            >
              <el-table-column prop="word_pair" label="词对" width="160">
                <template #default="{ row }">
                  <span :style="{ fontWeight: row.linkable ? 700 : 400 }">
                    {{ row.word_pair }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="连读条件" width="140" align="center">
                <template #default="{ row }">
                  <template v-if="row.linkable">
                    <span style="font-family:monospace;font-size:12px;color:var(--color-primary)">
                      {{ phonemeLabel(row.last_phoneme) }}
                    </span>
                    <span style="margin:0 4px;color:var(--color-text-disabled);">→</span>
                    <span style="font-family:monospace;font-size:12px;color:var(--color-success)">
                      {{ phonemeLabel(row.first_phoneme) }}
                    </span>
                  </template>
                  <span v-else class="text-muted">无</span>
                </template>
              </el-table-column>
              <el-table-column prop="gap_ms" label="词间间隙" width="100" align="center">
                <template #default="{ row }">
                  <span
                    :style="{
                      color: row.gap_ms <= 30 ? 'var(--color-success)' :
                             row.gap_ms <= 80 ? 'var(--color-warning)' :
                             'var(--color-danger)',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums',
                    }"
                  >{{ row.gap_ms }} ms</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="90" align="center">
                <template #default="{ row }">
                  <template v-if="!row.linkable">
                    <span class="text-muted">—</span>
                  </template>
                  <template v-else>
                    <span v-if="row.gap_ms <= 30" style="color:var(--color-success);font-size:12px;">◉ 连读</span>
                    <span v-else-if="row.gap_ms <= 80" style="color:var(--color-warning);font-size:12px;">◑ 弱连</span>
                    <span v-else style="color:var(--color-danger);font-size:12px;">○ 断开</span>
                  </template>
                </template>
              </el-table-column>
              <el-table-column label="得分" width="80" align="center">
                <template #default="{ row }">
                  <span
                    :style="{
                      color: row.score >= 80 ? 'var(--color-success)' :
                             row.score >= 60 ? 'var(--color-warning)' :
                             'var(--color-danger)',
                      fontWeight: 600,
                    }"
                  >{{ row.score }}</span>
                </template>
              </el-table-column>
            </el-table>
            <p v-else class="text-muted">词数不足，无法分析连读</p>

            <!-- 模型输出数据 -->
            <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
            <div class="model-data-grid">
              <div class="model-data-item">
                <span class="data-label">平均词间间隙</span>
                <span class="data-value">{{ scoreResult.linking_viz?.avg_gap_ms ?? '-' }} ms</span>
                <span class="data-explain">{{ gapExplain(scoreResult.linking_viz?.avg_gap_ms) }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">可连读词对数</span>
                <span class="data-value">{{ scoreResult.linking_viz?.linkable_count ?? 0 }} 对</span>
                <span class="data-explain">满足辅音→元音连读条件的相邻词</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">实际连读词对数</span>
                <span class="data-value">{{ scoreResult.linking_viz?.linked_count ?? 0 }} 对</span>
                <span class="data-explain">间隙 ≤ 30ms 的词对</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">数据来源</span>
                <span class="data-value">WhisperX</span>
                <span class="data-explain">词级时间戳 + G2P 音素分类</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ===== 节奏感分析 ===== -->
        <el-tab-pane label="节奏感" name="rhythm">
          <div class="viz-section">
            <!-- 分析结论 -->
            <div class="model-insight">
              <el-icon :size="16"><InfoFilled /></el-icon>
              <span>{{ rhythmSummary }}</span>
            </div>

            <!-- 时长分布柱状图 -->
            <h4 class="viz-title">音素时长分布</h4>
            <div v-if="scoreResult.rhythm_viz?.chars?.length" class="rhythm-chart">
              <div
                v-for="(ch, i) in scoreResult.rhythm_viz.chars"
                :key="'rh'+i"
                class="rhythm-bar-col"
              >
                <div class="rhythm-bar-fill-wrap">
                  <div
                    class="rhythm-bar-fill"
                    :style="{
                      height: (scoreResult.rhythm_viz.durations_ms[i] / Math.max(...scoreResult.rhythm_viz.durations_ms) * 100) + '%',
                      background: scoreResult.rhythm_viz.is_pause[i]
                        ? 'var(--color-danger)'
                        : 'var(--color-primary)',
                    }"
                  />
                </div>
                <span
                  class="rhythm-bar-label"
                  :style="{ color: scoreResult.rhythm_viz.is_pause[i] ? 'var(--color-danger)' : 'var(--color-text-primary)' }"
                >{{ ch }}</span>
                <span class="rhythm-bar-ms">{{ scoreResult.rhythm_viz.durations_ms[i] }}ms</span>
              </div>
            </div>
            <p v-else class="text-muted">时长数据不足</p>

            <div class="viz-legend">
              <span class="legend-dot" style="background:var(--color-primary)"></span> 正常音素
              <span class="legend-dot" style="background:var(--color-danger)"></span> 异常停顿 (&gt;2x 均值)
            </div>

            <!-- 模型输出数据 -->
            <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
            <div class="model-data-grid">
              <div class="model-data-item">
                <span class="data-label">平均音素时长</span>
                <span class="data-value">{{ scoreResult.rhythm_viz?.mean_ms ?? '-' }} ms</span>
                <span class="data-explain">所有音素时长的算术平均</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">时长标准差</span>
                <span class="data-value">{{ scoreResult.rhythm_viz?.std_ms ?? '-' }} ms</span>
                <span class="data-explain">音素时长离散程度</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">变异系数 (CV)</span>
                <span class="data-value">{{ scoreResult.rhythm_viz?.cv ?? '-' }}</span>
                <span class="data-explain">{{ rhythmCVExplain(scoreResult.rhythm_viz?.cv) }}</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">异常停顿数</span>
                <span class="data-value">{{ scoreResult.rhythm_viz?.pause_count ?? 0 }} 处</span>
                <span class="data-explain">时长 &gt; 2x 均值的音素（阈值 {{ (scoreResult.rhythm_viz?.mean_ms || 0) * 2 | 0 }}ms）</span>
              </div>
              <div class="model-data-item" v-if="pauseSlots.length > 0">
                <span class="data-label">卡顿位置</span>
                <span class="data-value" style="color:var(--color-danger);">
                  {{ pauseSlots.map(p => `${p.char}(${p.dur}ms)`).join(', ') }}
                </span>
                <span class="data-explain">异常卡顿的音素及时长</span>
              </div>
              <div class="model-data-item">
                <span class="data-label">数据来源</span>
                <span class="data-value">CTC 强制对齐</span>
                <span class="data-explain">wav2vec2 Viterbi 对齐输出</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="评分算法说明" name="explain">
          <div class="explain-section">
            <el-collapse>
              <el-collapse-item title="wav2vec2 是什么？" name="1">
                <p>wav2vec2 是 Meta 开业的语音特征提取模型（Apache 2.0 开源协议），在 960 小时英语语音数据上训练。它将音频波形转换为每 20ms 一帧的概率分布，预测每个时刻正在发哪个音。</p>
              </el-collapse-item>

              <el-collapse-item title="GOP 是什么？" name="2">
                <p>GOP（Goodness of Pronunciation，发音优良度）是一种无参考发音评测算法。它不需要标准发音音频，而是计算：</p>
                <div class="formula-box">
                  GOP = log( P(正确音素 | 声学特征) ) / 持续时长
                </div>
                <p>简单说：模型根据你的声音推断每个音素的「后验概率」，概率越高说明发音越接近模型见过的标准发音。</p>
              </el-collapse-item>

              <el-collapse-item title="评分流程" name="3">
                <div class="pipeline-steps">
                  <div class="pipeline-step">
                    <span class="step-num">1</span>
                    <div>
                      <strong>音频输入</strong>
                      <p>浏览器录音 → ffmpeg 转码为 16kHz 单声道 WAV</p>
                    </div>
                  </div>
                  <div class="pipeline-step">
                    <span class="step-num">2</span>
                    <div>
                      <strong>wav2vec2 特征提取</strong>
                      <p>模型将每 20ms 音频帧映射为字符级后验概率分布（A-Z, 空格）</p>
                    </div>
                  </div>
                  <div class="pipeline-step">
                    <span class="step-num">3</span>
                    <div>
                      <strong>CTC 强制对齐</strong>
                      <p>Viterbi 算法在概率矩阵上找到文本对应的最优时间路径，锁定每个字符在音频中的精确位置</p>
                    </div>
                  </div>
                  <div class="pipeline-step">
                    <span class="step-num">4</span>
                    <div>
                      <strong>GOP 打分</strong>
                      <p>对每个字符所在帧的后验概率取均值，映射为 0-100 分数</p>
                    </div>
                  </div>
                </div>
              </el-collapse-item>

              <el-collapse-item title="评级标准" name="4">
                <el-table :data="levelTable" size="small" style="margin-top: 8px;">
                  <el-table-column prop="range" label="分数范围" width="120" />
                  <el-table-column prop="level" label="评级" width="100" />
                  <el-table-column prop="desc" label="说明" />
                </el-table>
              </el-collapse-item>

              <el-collapse-item title="当前版本限制" name="5">
                <ul class="limit-list">
                  <li>模型输出为<b>字符级</b>（A-Z），不是音素级（IPA），因此「T」「A」等字母得分代表该字母对应发音的质量</li>
                  <li>流利度<b>暂未实现</b>，计划基于 WhisperX 语速+停顿分析</li>
                  <li>分数受录音环境影响（背景噪音会降低置信度）</li>
                  <li>建议在<b>安静环境</b>下使用以获得准确评分</li>
                </ul>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button type="primary" @click="showDetail = false; nextContent()">
          下一题
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </template>
    </el-dialog>

    <!-- 隐藏的音频元素（用于播放控制） -->
    <audio
      v-if="recordingUrl"
      ref="userAudioRef"
      :src="recordingUrl"
      @play="userPlaying = true"
      @pause="userPlaying = false"
      @ended="userPlaying = false"
      @timeupdate="onUserTimeUpdate"
      @loadedmetadata="onUserTimeUpdate"
      style="display:none"
    />
    <audio
      v-if="referenceUrl"
      ref="refAudioRef"
      :src="referenceUrl"
      @play="refPlaying = true"
      @pause="refPlaying = false"
      @ended="refPlaying = false"
      @timeupdate="onRefTimeUpdate"
      @loadedmetadata="onRefTimeUpdate"
      style="display:none"
    />
  </div>
</template>

<style lang="scss" scoped>
.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.control-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.control-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

// 跟读内容
.content-display {
  background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.04), rgba(var(--color-primary-rgb), 0.08));
  border: 1px solid rgba(var(--color-primary-rgb), 0.15);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xxl);
  text-align: center;
  margin-bottom: var(--spacing-xxl);
}

.content-main {
  margin-bottom: var(--spacing-sm);

  .word-text {
    font-size: 36px;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  .sentence-text {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.6;
  }
}

.content-ipa {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  font-family: 'Segoe UI', serif;
}

.content-chinese {
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-md);
}

.play-btn {
  margin-top: var(--spacing-sm);
}

// 录音区域
.record-section {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xxl) 0;
}

// 评分结果
.score-section {
  margin-top: var(--spacing-xl);
}

.score-divider {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);

  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--color-border);
  }
}

.overall-score {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xl);

  .overall-number {
    font-size: 48px;
    font-weight: 800;
    line-height: 1;
  }

  .overall-unit {
    font-size: var(--font-size-lg);
    margin-right: var(--spacing-sm);
  }
}

// 错误音素
.error-section {
  margin: var(--spacing-xl) 0;
  padding: var(--spacing-lg);
  background: rgba(var(--color-danger-rgb), 0.04);
  border: 1px solid rgba(var(--color-danger-rgb), 0.12);
  border-radius: var(--radius-md);

  h4 {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: var(--spacing-md);
  }
}

.error-item {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);

  &:last-child {
    margin-bottom: 0;
  }
}

.error-phoneme {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.error-actual {
  font-size: var(--font-size-base);
  color: var(--color-danger);
  font-family: 'Segoe UI', monospace;
}

.error-tip {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

// ========== 对比播放器 ==========
.compare-players {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
}

.player-card {
  flex: 1;
  min-width: 0;
}

.player-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.player-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.player-dot-user {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
  display: inline-block;
}

.player-dot-ref {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  display: inline-block;
}

.player-time {
  font-size: 11px;
  font-family: 'SF Mono', 'Menlo', monospace;
  color: var(--color-text-disabled);
  font-variant-numeric: tabular-nums;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.player-play-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, box-shadow 0.15s;
  font-size: 14px;

  &:hover {
    transform: scale(1.08);
    box-shadow: 0 2px 8px rgba(var(--color-primary-rgb), 0.3);
  }

  &:active {
    transform: scale(0.95);
  }
}

.play-icon {
  line-height: 1;
}

.player-wave {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  height: 36px;
  min-width: 0;
}

.wave-bar {
  flex: 1;
  min-width: 2px;
  max-width: 6px;
  background: var(--color-primary);
  border-radius: 2px;
  transition: height 0.08s ease;
  opacity: 0.7;
}

.vs-badge {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-primary);
  border: 2px solid var(--color-border);
  font-size: 10px;
  font-weight: 800;
  color: var(--color-text-disabled);
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
}

// 查看详情按钮
.detail-trigger {
  text-align: center;
  margin: var(--spacing-lg) 0;
}

// ========== 详细评分弹窗 ==========
:deep(.score-dialog) {
  .el-dialog__body {
    max-height: 82vh;
    overflow-y: auto;
    padding-top: var(--spacing-md);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.dialog-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.detail-overview {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxl);
}

.detail-score-ring {
  flex-shrink: 0;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  border: 4px solid currentColor;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.ring-number {
  font-size: 28px;
  font-weight: 800;
}

.ring-unit {
  font-size: var(--font-size-xs);
  opacity: 0.7;
}

.detail-overview-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.overview-text-item {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;

  strong {
    color: var(--color-text-primary);
  }
}

// 维度分析说明
.detail-insights {
  margin-top: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(var(--color-primary-rgb), 0.03);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);

  strong {
    color: var(--color-text-primary);
  }

  .el-icon {
    color: var(--color-primary);
    margin-top: 2px;
    flex-shrink: 0;
  }
}

// 音素色块条
.phoneme-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.phoneme-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1.5px solid;
  min-width: 44px;
}

.chip-char {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.chip-score {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.text-muted {
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);
}

// ========== 可视化分析 Tab ==========
.viz-section {
  .viz-title {
    font-size: var(--font-size-sm);
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: var(--spacing-md);
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }
}

// 重音能量柱状图
.stress-chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 120px;
  padding: 8px 0;
}

.stress-bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
}

.stress-bar-fill-wrap {
  flex: 1;
  width: 100%;
  max-width: 32px;
  border-radius: 4px 4px 0 0;
  background: var(--color-bg-secondary);
  position: relative;
  overflow: hidden;
}

.stress-bar-fill {
  position: absolute;
  bottom: 0;
  width: 100%;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
  min-height: 2px;
}

.stress-bar-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: lowercase;
}

.viz-legend {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 4px;
}

.viz-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  margin-top: var(--spacing-sm);
}

// 节奏感时长分布图
.rhythm-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 120px;
  padding: 8px 0;
}

.rhythm-bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  min-width: 0;
}

.rhythm-bar-fill-wrap {
  flex: 1;
  width: 100%;
  max-width: 28px;
  border-radius: 4px 4px 0 0;
  background: var(--color-bg-secondary);
  position: relative;
  overflow: hidden;
}

.rhythm-bar-fill {
  position: absolute;
  bottom: 0;
  width: 100%;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
  min-height: 2px;
}

.rhythm-bar-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: lowercase;
}

.rhythm-bar-ms {
  font-size: 9px;
  color: var(--color-text-disabled);
  font-variant-numeric: tabular-nums;
}

// 语调曲线
.intonation-chart {
  padding: var(--spacing-md) 0;
}

.intonation-direction {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.direction-arrow {
  font-size: 24px;
  display: inline-block;
  transition: transform 0.3s;
}

.direction-label {
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--color-text-primary);
}

.direction-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  margin-left: auto;
}

.f0-curve-svg {
  width: 100%;
  height: 100px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

// 模型分析结论卡片
.model-insight {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: rgba(var(--color-primary-rgb), 0.05);
  border: 1px solid rgba(var(--color-primary-rgb), 0.12);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);

  .el-icon {
    color: var(--color-primary);
    margin-top: 1px;
    flex-shrink: 0;
  }
}

// 模型输出数据网格
.model-data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
}

.model-data-item {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.data-label {
  font-size: 11px;
  color: var(--color-text-disabled);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-value {
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

.data-explain {
  font-size: 11px;
  color: var(--color-text-disabled);
  line-height: 1.4;
}

.intonation-expect {
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  margin-left: auto;
}

// 评分说明
.explain-section {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;

  p {
    margin: 0 0 var(--spacing-sm);
  }
}

.formula-box {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--font-size-sm);
  text-align: center;
  margin: var(--spacing-md) 0;
  color: var(--color-primary);
  font-weight: 600;
}

.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.pipeline-step {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;

  .step-num {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--color-primary);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 2px;
  }

  strong {
    display: block;
    color: var(--color-text-primary);
    font-size: var(--font-size-sm);
    margin-bottom: 2px;
  }

  p {
    margin: 0;
    font-size: var(--font-size-xs);
  }
}

.limit-list {
  padding-left: var(--spacing-lg);
  margin: 0;

  li {
    margin-bottom: var(--spacing-xs);
    font-size: var(--font-size-sm);

    b {
      color: var(--color-text-primary);
    }
  }
}
</style>
