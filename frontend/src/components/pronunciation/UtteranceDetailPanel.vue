<script setup>
import { computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  pronunciationData: { type: Object, required: true },
  text: { type: String, default: '' },
})

const data = computed(() => props.pronunciationData || {})

// 评分等级
const scoreLevel = computed(() => {
  const s = data.value?.overall || 0
  if (s >= 80) return { label: '优秀', type: 'success' }
  if (s >= 60) return { label: '良好', type: 'warning' }
  return { label: '需加强', type: 'danger' }
})

function getScoreColor(score) {
  if (score >= 80) return '#5AD8A6'
  if (score >= 60) return '#F6BD16'
  return '#FF6B8A'
}

function getCharScoreBg(score) {
  if (score >= 80) return 'rgba(90,216,166,0.15)'
  if (score >= 60) return 'rgba(246,189,22,0.15)'
  if (score >= 40) return 'rgba(246,189,22,0.08)'
  return 'rgba(255,107,138,0.12)'
}

function getCharScoreBorder(score) {
  if (score >= 80) return '#5AD8A6'
  if (score >= 60) return '#F6BD16'
  if (score >= 40) return '#F6BD16'
  return '#FF6B8A'
}

// 重音
const stressCount = computed(() => (data.value?.stress_viz?.is_stressed || []).filter(Boolean).length)
const stressChars = computed(() => {
  const viz = data.value?.stress_viz
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

// 语调
const sentenceTypeLabel = computed(() => {
  const t = data.value?.intonation_viz?.sentence_type
  if (t === 'question') return '疑问句'
  if (t === 'exclamation') return '感叹句'
  return '陈述句'
})

const expectedIntonation = computed(() => {
  const t = data.value?.intonation_viz?.sentence_type
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

// 连读
const linkingPairs = computed(() => data.value?.linking_viz?.pairs || [])
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

// 节奏
function rhythmCVExplain(cv) {
  if (cv == null) return ''
  if (cv < 0.15) return '→ 过于均匀，像机器人发音'
  if (cv < 0.30) return '→ 节奏自然流畅，符合英语轻重节拍'
  if (cv < 0.50) return '→ 有些波动，基本可接受'
  if (cv < 0.80) return '→ 节奏不够稳定，时快时慢'
  return '→ 节奏非常不均匀，影响可懂度'
}

const pauseSlots = computed(() => {
  const viz = data.value?.rhythm_viz
  if (!viz?.is_pause) return []
  return viz.is_pause.map((pause, i) => pause ? { char: viz.chars[i], dur: viz.durations_ms[i] } : null).filter(Boolean)
})

const rhythmSummary = computed(() => {
  const viz = data.value?.rhythm_viz
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

const levelTable = [
  { range: '80 - 100', level: '优秀', desc: '发音近似母语者，音素清晰准确' },
  { range: '60 - 79', level: '良好', desc: '基本正确，个别音素可改进' },
  { range: '40 - 59', level: '一般', desc: '部分音素偏差较大，需针对性练习' },
  { range: '0 - 39', level: '需练习', desc: '多数音素与标准发音差距明显，建议从基础音标练起' },
]
</script>

<template>
  <div class="utterance-detail" v-if="data">
    <!-- 头部概览 -->
    <div class="detail-overview">
      <div class="detail-score-ring" :style="{ color: getScoreColor(data.overall) }">
        <span class="ring-number">{{ data.overall }}</span>
        <span class="ring-unit">/100</span>
      </div>
      <div class="detail-overview-text">
        <p class="overview-text-item">评测文本：<strong>{{ text }}</strong></p>
        <p class="overview-text-item">评分音素：<strong>{{ data.char_scores?.length || 0 }}</strong> 个</p>
        <p class="overview-text-item">问题音素：<strong>{{ data.errors?.length || 0 }}</strong> 个</p>
      </div>
    </div>

    <!-- 维度分析说明 -->
    <div v-if="data.analysis_detail" class="detail-insights">
      <div class="insight-item">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>重音：{{ data.analysis_detail.stress || '无数据' }}</span>
      </div>
      <div class="insight-item">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>语调：{{ data.analysis_detail.intonation || '无数据' }}</span>
      </div>
      <div class="insight-item">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>连读：{{ data.analysis_detail.linking || '无数据' }}</span>
      </div>
    </div>

    <el-tabs model-value="phoneme">
      <!-- 逐音素评分 -->
      <el-tab-pane label="逐音素评分" name="phoneme">
        <div class="phoneme-strip">
          <el-tooltip
            v-for="(cs, i) in data.char_scores"
            :key="i"
            :content="cs.tip || ''"
            placement="top"
            effect="dark"
            :disabled="!cs.tip"
          >
            <div
              class="phoneme-chip"
              :class="{ 'phoneme-chip--has-tip': cs.tip }"
              :style="{ background: getCharScoreBg(cs.score), borderColor: getCharScoreBorder(cs.score) }"
            >
              <span class="chip-char">{{ cs.char }}</span>
              <span class="chip-score">{{ cs.score }}</span>
            </div>
          </el-tooltip>
          <p v-if="!data.char_scores?.length" class="text-muted">暂无逐音素数据</p>
        </div>

        <el-table
          v-if="data.char_scores?.length"
          :data="data.char_scores"
          size="small"
          stripe
          max-height="300"
          style="margin-top: 16px;"
        >
          <el-table-column prop="char" label="音素" width="80" align="center" />
          <el-table-column prop="score" label="GOP 得分" width="120" align="center">
            <template #default="{ row }">
              <span :style="{ color: getScoreColor(row.score), fontWeight: 600 }">{{ row.score }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration_ms" label="时长(ms)" width="100" align="center" />
          <el-table-column prop="level" label="评级" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.score >= 80 ? 'success' : row.score >= 60 ? 'warning' : 'danger'"
                size="small"
              >{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" min-width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.min(row.score, 100)"
                :color="row.score >= 80 ? '#5AD8A6' : row.score >= 60 ? '#F6BD16' : '#FF6B8A'"
                :stroke-width="8"
                :show-text="false"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 重音位置分析 -->
      <el-tab-pane label="重音位置分析" name="stress">
        <div class="viz-section">
          <div class="model-insight">
            <el-icon :size="16"><InfoFilled /></el-icon>
            <span>{{ data.analysis_detail?.stress || '无分析数据' }}</span>
          </div>

          <h4 class="viz-title">音素能量分布</h4>
          <div v-if="data.stress_viz?.chars?.length" class="stress-chart">
            <div v-for="(ch, i) in data.stress_viz.chars" :key="'s'+i" class="stress-bar-col">
              <div class="stress-bar-fill-wrap">
                <div
                  class="stress-bar-fill"
                  :style="{
                    height: (data.stress_viz.energies[i] * 100) + '%',
                    background: data.stress_viz.is_stressed[i] ? '#7C6FF7' : '#ddd',
                  }"
                />
              </div>
              <span
                class="stress-bar-label"
                :style="{
                  color: data.stress_viz.is_stressed[i] ? '#7C6FF7' : '#999',
                  fontWeight: data.stress_viz.is_stressed[i] ? 700 : 400,
                }"
              >{{ ch }}</span>
            </div>
          </div>
          <div class="viz-legend">
            <span class="legend-dot" style="background:#7C6FF7"></span> 重读音节
            <span class="legend-dot" style="background:#ddd"></span> 非重读音节
          </div>

          <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
          <div class="model-data-grid">
            <div class="model-data-item">
              <span class="data-label">能量变异系数 (CV)</span>
              <span class="data-value">{{ data.stress_viz?.energy_cv ?? '-' }}</span>
              <span class="data-explain">{{ stressCVExplain(data.stress_viz?.energy_cv) }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">时长变异系数 (CV)</span>
              <span class="data-value">{{ data.stress_viz?.dur_cv ?? '-' }}</span>
              <span class="data-explain">{{ durCVExplain(data.stress_viz?.dur_cv) }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">检测到重读音节</span>
              <span class="data-value">{{ stressCount }} 个</span>
              <span class="data-explain">{{ stressChars }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">归一化能量序列</span>
              <span class="data-value" style="font-size:11px;font-family:monospace;">[{{ (data.stress_viz?.energies || []).map(v => v.toFixed(2)).join(', ') }}]</span>
              <span class="data-explain">0~1 归一化，值越大能量越强</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 语调曲线分析 -->
      <el-tab-pane label="语调曲线分析" name="intonation">
        <div class="viz-section">
          <div class="model-insight">
            <el-icon :size="16"><InfoFilled /></el-icon>
            <span>{{ data.analysis_detail?.intonation || '无分析数据' }}</span>
          </div>

          <h4 class="viz-title">
            F0 基频曲线
            <el-tag size="small" :type="data.intonation_viz?.sentence_type === 'question' ? 'warning' : 'primary'">
              {{ sentenceTypeLabel }}
            </el-tag>
            <span class="intonation-expect">预期: {{ expectedIntonation }}</span>
          </h4>

          <div v-if="data.intonation_viz?.f0_points?.length" class="intonation-chart">
            <div class="intonation-direction">
              <span class="direction-arrow" :style="{
                transform: data.intonation_viz.slope_st_per_sec > 0.2 ? 'rotate(-45deg)' : data.intonation_viz.slope_st_per_sec < -0.2 ? 'rotate(45deg)' : 'rotate(0deg)',
              }">➤</span>
              <span class="direction-label">{{ data.intonation_viz.direction }}</span>
            </div>
            <svg
              v-if="data.intonation_viz.f0_points.length > 1"
              class="f0-curve-svg"
              :viewBox="`0 0 ${data.intonation_viz.f0_points.length * 12} 100`"
            >
              <polyline
                :points="data.intonation_viz.f0_points.map((p, i) => {
                  const hzMin = Math.min(...data.intonation_viz.f0_points.map(x => x.hz))
                  const hzMax = Math.max(...data.intonation_viz.f0_points.map(x => x.hz))
                  const range = hzMax - hzMin || 1
                  const y = 95 - ((p.hz - hzMin) / range) * 80
                  return `${i * 12 + 6},${y}`
                }).join(' ')"
                fill="none"
                stroke="#7C6FF7"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <p v-else class="text-muted">基频数据不足，无法绘制曲线</p>

          <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
          <div class="model-data-grid">
            <div class="model-data-item">
              <span class="data-label">基频斜率 (F0 Slope)</span>
              <span class="data-value">{{ data.intonation_viz?.slope_st_per_sec ?? '-' }} st/s</span>
              <span class="data-explain">正值=升调，负值=降调，接近0=平调</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">音高范围 (F0 Range)</span>
              <span class="data-value">{{ data.intonation_viz?.range_st ?? '-' }} 半音</span>
              <span class="data-explain">{{ rangeExplain(data.intonation_viz?.range_st) }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">基频采样点数</span>
              <span class="data-value">{{ data.intonation_viz?.f0_points?.length || 0 }} 帧</span>
              <span class="data-explain">PYIN 算法提取的有声音帧</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">句类判断</span>
              <span class="data-value">{{ sentenceTypeLabel }}</span>
              <span class="data-explain">预期: {{ expectedIntonation }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 连读表现 -->
      <el-tab-pane label="连读表现" name="linking">
        <div class="viz-section">
          <div class="model-insight">
            <el-icon :size="16"><InfoFilled /></el-icon>
            <span>{{ data.analysis_detail?.linking || '无分析数据' }}</span>
          </div>

          <h4 class="viz-title">
            词间连读分析
            <el-tag size="small" :type="linkablePairs.length > 0 ? 'warning' : 'info'">
              {{ linkablePairs.length }} 处可连读
            </el-tag>
            <el-tag
              v-if="linkablePairs.length > 0"
              size="small"
              :type="linkedPairs.length >= linkablePairs.length * 0.7 ? 'success' : 'warning'"
            >{{ linkedPairs.length }} 处已连上</el-tag>
          </h4>

          <el-table v-if="linkingPairs.length > 0" :data="linkingPairs" size="small" stripe max-height="280">
            <el-table-column prop="word_pair" label="词对" width="160">
              <template #default="{ row }">
                <span :style="{ fontWeight: row.linkable ? 700 : 400 }">{{ row.word_pair }}</span>
              </template>
            </el-table-column>
            <el-table-column label="连读条件" width="140" align="center">
              <template #default="{ row }">
                <template v-if="row.linkable">
                  <span style="font-family:monospace;font-size:12px;color:#7C6FF7">{{ phonemeLabel(row.last_phoneme) }}</span>
                  <span style="margin:0 4px;color:#ccc;">→</span>
                  <span style="font-family:monospace;font-size:12px;color:#5AD8A6">{{ phonemeLabel(row.first_phoneme) }}</span>
                </template>
                <span v-else class="text-muted">无</span>
              </template>
            </el-table-column>
            <el-table-column prop="gap_ms" label="词间间隙" width="100" align="center">
              <template #default="{ row }">
                <span :style="{
                  color: row.gap_ms <= 30 ? '#5AD8A6' : row.gap_ms <= 80 ? '#F6BD16' : '#FF6B8A',
                  fontWeight: 600,
                }">{{ row.gap_ms }} ms</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <template v-if="!row.linkable"><span class="text-muted">—</span></template>
                <template v-else>
                  <span v-if="row.gap_ms <= 30" style="color:#5AD8A6;font-size:12px;">◉ 连读</span>
                  <span v-else-if="row.gap_ms <= 80" style="color:#F6BD16;font-size:12px;">◑ 弱连</span>
                  <span v-else style="color:#FF6B8A;font-size:12px;">○ 断开</span>
                </template>
              </template>
            </el-table-column>
            <el-table-column label="得分" width="80" align="center">
              <template #default="{ row }">
                <span :style="{
                  color: row.score >= 80 ? '#5AD8A6' : row.score >= 60 ? '#F6BD16' : '#FF6B8A',
                  fontWeight: 600,
                }">{{ row.score }}</span>
              </template>
            </el-table-column>
          </el-table>
          <p v-else class="text-muted">词数不足，无法分析连读</p>

          <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
          <div class="model-data-grid">
            <div class="model-data-item">
              <span class="data-label">平均词间间隙</span>
              <span class="data-value">{{ data.linking_viz?.avg_gap_ms ?? '-' }} ms</span>
              <span class="data-explain">{{ gapExplain(data.linking_viz?.avg_gap_ms) }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">可连读词对数</span>
              <span class="data-value">{{ data.linking_viz?.linkable_count ?? 0 }} 对</span>
              <span class="data-explain">满足辅音→元音连读条件的相邻词</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">实际连读词对数</span>
              <span class="data-value">{{ data.linking_viz?.linked_count ?? 0 }} 对</span>
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

      <!-- 节奏感 -->
      <el-tab-pane label="节奏感" name="rhythm">
        <div class="viz-section">
          <div class="model-insight">
            <el-icon :size="16"><InfoFilled /></el-icon>
            <span>{{ rhythmSummary }}</span>
          </div>

          <h4 class="viz-title">音素时长分布</h4>
          <div v-if="data.rhythm_viz?.chars?.length" class="rhythm-chart">
            <div v-for="(ch, i) in data.rhythm_viz.chars" :key="'rh'+i" class="rhythm-bar-col">
              <div class="rhythm-bar-fill-wrap">
                <div
                  class="rhythm-bar-fill"
                  :style="{
                    height: (data.rhythm_viz.durations_ms[i] / Math.max(...data.rhythm_viz.durations_ms) * 100) + '%',
                    background: data.rhythm_viz.is_pause[i] ? '#FF6B8A' : '#7C6FF7',
                  }"
                />
              </div>
              <span
                class="rhythm-bar-label"
                :style="{ color: data.rhythm_viz.is_pause[i] ? '#FF6B8A' : '#4A4A5A' }"
              >{{ ch }}</span>
              <span class="rhythm-bar-ms">{{ data.rhythm_viz.durations_ms[i] }}ms</span>
            </div>
          </div>
          <p v-else class="text-muted">时长数据不足</p>

          <div class="viz-legend">
            <span class="legend-dot" style="background:#7C6FF7"></span> 正常音素
            <span class="legend-dot" style="background:#FF6B8A"></span> 异常停顿 (&gt;2x 均值)
          </div>

          <h4 class="viz-title" style="margin-top: 20px;">模型输出数据</h4>
          <div class="model-data-grid">
            <div class="model-data-item">
              <span class="data-label">平均音素时长</span>
              <span class="data-value">{{ data.rhythm_viz?.mean_ms ?? '-' }} ms</span>
              <span class="data-explain">所有音素时长的算术平均</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">时长标准差</span>
              <span class="data-value">{{ data.rhythm_viz?.std_ms ?? '-' }} ms</span>
              <span class="data-explain">音素时长离散程度</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">变异系数 (CV)</span>
              <span class="data-value">{{ data.rhythm_viz?.cv ?? '-' }}</span>
              <span class="data-explain">{{ rhythmCVExplain(data.rhythm_viz?.cv) }}</span>
            </div>
            <div class="model-data-item">
              <span class="data-label">异常停顿数</span>
              <span class="data-value">{{ data.rhythm_viz?.pause_count ?? 0 }} 处</span>
              <span class="data-explain">时长 &gt; 2x 均值的音素</span>
            </div>
            <div class="model-data-item" v-if="pauseSlots.length > 0">
              <span class="data-label">卡顿位置</span>
              <span class="data-value" style="color:#FF6B8A;">
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

      <!-- 评分算法说明 -->
      <el-tab-pane label="评分算法说明" name="explain">
        <div class="explain-section">
          <el-collapse>
            <el-collapse-item title="wav2vec2 是什么？" name="1">
              <p>wav2vec2 是 Meta 开源的语音特征提取模型（Apache 2.0），在 960 小时英语语音数据上训练。它将音频波形转换为每 20ms 一帧的概率分布，预测每个时刻正在发哪个音。</p>
            </el-collapse-item>
            <el-collapse-item title="GOP 是什么？" name="2">
              <p>GOP（Goodness of Pronunciation）是无参考发音评测算法，计算每个音素的后验概率：</p>
              <div class="formula-box">GOP = log( P(正确音素 | 声学特征) ) / 持续时长</div>
              <p>概率越高说明发音越接近模型见过的标准发音。</p>
            </el-collapse-item>
            <el-collapse-item title="评分流程" name="3">
              <div class="pipeline-steps">
                <div class="pipeline-step"><span class="step-num">1</span><div><strong>音频输入</strong><p>浏览器录音 → ffmpeg 转码为 16kHz 单声道 WAV</p></div></div>
                <div class="pipeline-step"><span class="step-num">2</span><div><strong>wav2vec2 特征提取</strong><p>模型将每 20ms 音频帧映射为字符级后验概率分布</p></div></div>
                <div class="pipeline-step"><span class="step-num">3</span><div><strong>CTC 强制对齐</strong><p>Viterbi 算法在概率矩阵上找到文本对应的最优时间路径</p></div></div>
                <div class="pipeline-step"><span class="step-num">4</span><div><strong>GOP 打分</strong><p>对每个字符所在帧的后验概率取均值，映射为 0-100 分数</p></div></div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="评级标准" name="4">
              <el-table :data="levelTable" size="small" style="margin-top: 8px;">
                <el-table-column prop="range" label="分数范围" width="120" />
                <el-table-column prop="level" label="评级" width="100" />
                <el-table-column prop="desc" label="说明" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
.utterance-detail {
  padding: 16px 0;
}

.detail-overview {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
  padding: 16px;
  background: #F8F0FF;
  border-radius: 16px;
}

.detail-score-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid currentColor;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .ring-number { font-size: 28px; font-weight: 800; line-height: 1; }
  .ring-unit { font-size: 11px; opacity: 0.7; }
}

.detail-overview-text {
  font-size: 13px;
  color: #666;
  line-height: 1.8;
  strong { color: #3D3D5C; }
}

.detail-insights {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #F0F8FF;
  border-radius: 12px;
  font-size: 13px;
  color: #5B8FF9;

  .insight-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
  }
}

.phoneme-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.phoneme-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1.5px solid;
  min-width: 44px;

  .chip-char { font-size: 14px; font-weight: 700; color: #3D3D5C; }
  .chip-score { font-size: 10px; color: #999; }
}

.phoneme-chip--has-tip {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.viz-section {
  .model-insight {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 12px 16px;
    background: #F0F8FF;
    border-radius: 12px;
    font-size: 13px;
    color: #5B8FF9;
    margin-bottom: 16px;
  }
}

.viz-title {
  font-size: 14px;
  font-weight: 600;
  color: #3D3D5C;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.intonation-expect {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.stress-chart, .rhythm-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 140px;
  padding: 8px 0;
  overflow-x: auto;
}

.stress-bar-col, .rhythm-bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 28px;
}

.stress-bar-fill-wrap, .rhythm-bar-fill-wrap {
  width: 100%;
  height: 100px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.stress-bar-fill, .rhythm-bar-fill {
  width: 20px;
  border-radius: 4px 4px 0 0;
  min-height: 2px;
  transition: height 0.4s ease;
}

.stress-bar-label, .rhythm-bar-label {
  font-size: 11px;
  margin-top: 4px;
  font-weight: 600;
}

.rhythm-bar-ms {
  font-size: 9px;
  color: #aaa;
  margin-top: 2px;
}

.viz-legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 12px;
  color: #999;

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 4px;
  }
}

.intonation-chart {
  margin: 12px 0;
}

.intonation-direction {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #7C6FF7;
}

.direction-arrow {
  display: inline-block;
  font-size: 18px;
  transition: transform 0.3s;
}

.f0-curve-svg {
  width: 100%;
  height: 100px;
  background: #F8F0FF;
  border-radius: 8px;
}

.model-data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.model-data-item {
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 10px;

  .data-label { font-size: 11px; color: #999; display: block; margin-bottom: 4px; }
  .data-value { font-size: 15px; font-weight: 700; color: #3D3D5C; display: block; margin-bottom: 2px; }
  .data-explain { font-size: 11px; color: #aaa; }
}

.explain-section {
  font-size: 13px;
  color: #666;
  line-height: 1.7;
}

.formula-box {
  background: #F8F0FF;
  padding: 10px 16px;
  border-radius: 8px;
  font-family: monospace;
  font-size: 13px;
  color: #7C6FF7;
  text-align: center;
  margin: 8px 0;
}

.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pipeline-step {
  display: flex;
  gap: 12px;
  align-items: flex-start;

  .step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #7C6FF7;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  strong { color: #3D3D5C; }
  p { color: #999; font-size: 12px; margin-top: 2px; }
}

.text-muted { color: #ccc; font-size: 13px; text-align: center; padding: 20px; }
</style>