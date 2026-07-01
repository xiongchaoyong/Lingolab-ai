<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Headset, VideoPlay, VideoPause, CircleCheck, ArrowLeft } from '@element-plus/icons-vue'
import { getMaterialDetailApi } from '@/api/recommendation'
import { completeTaskApi, getDailyTasksApi } from '@/api/learning_path'

const router = useRouter()
const route = useRoute()

const taskId = computed(() => Number(route.query.taskId) || 0)

// 阶段：ready → listening → complete
const phase = ref('ready') // 'ready' | 'listening' | 'complete'

// 资料信息
const material = ref(null)
const loading = ref(false)
const materialError = ref('')

// 音频播放
const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const audioDuration = ref(0)
const listenStartTime = ref(null)
const totalListenSeconds = ref(0)

// 完成状态
const completing = ref(false)

const progressPercent = computed(() => {
  if (audioDuration.value <= 0) return 0
  return (currentTime.value / audioDuration.value) * 100
})

const formattedCurrentTime = computed(() => formatTime(currentTime.value))
const formattedDuration = computed(() => formatTime(audioDuration.value))
const formattedListenTime = computed(() => formatTime(totalListenSeconds.value))

function formatTime(seconds) {
  if (!seconds || seconds <= 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

async function fetchMaterial() {
  if (!taskId.value) {
    materialError.value = '缺少任务 ID'
    return
  }

  loading.value = true
  try {
    // 获取任务信息来拿到 material_id
    const tasksRes = await getDailyTasksApi()
    const task = tasksRes.tasks?.find(t => t.id === taskId.value)
    if (!task) {
      materialError.value = '任务不存在'
      return
    }

    // 获取资料详情
    const matRes = await getMaterialDetailApi(task.material_id || task.id)
    material.value = matRes
  } catch (e) {
    materialError.value = '加载资料失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function startListening() {
  phase.value = 'listening'
  listenStartTime.value = Date.now()

  // 自动播放
  setTimeout(() => {
    if (audioRef.value) {
      audioRef.value.play().catch(() => {
        // 浏览器自动播放策略可能阻止，用户需手动点击
      })
    }
  }, 300)
}

function togglePlay() {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play().catch(() => {})
  }
}

function onTimeUpdate() {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

function onLoadedMetadata() {
  if (audioRef.value) {
    audioDuration.value = audioRef.value.duration
  }
}

function onPlay() {
  isPlaying.value = true
}

function onPause() {
  isPlaying.value = false
}

function onEnded() {
  isPlaying.value = false
}

function finishListening() {
  // 计算实际听力时长
  if (listenStartTime.value) {
    totalListenSeconds.value = Math.round((Date.now() - listenStartTime.value) / 1000)
  }
  phase.value = 'complete'
}

async function completeTask() {
  if (!taskId.value) return

  completing.value = true
  try {
    await completeTaskApi(taskId.value, {
      duration_seconds: totalListenSeconds.value,
    })
    ElMessage.success('听力任务已完成！')
    router.push('/learning-path')
  } catch (e) {
    ElMessage.error('提交失败，请重试')
  } finally {
    completing.value = false
  }
}

function goBack() {
  if (phase.value === 'listening') {
    // 暂停音频
    if (audioRef.value) {
      audioRef.value.pause()
    }
    // 计算已听时长
    if (listenStartTime.value) {
      totalListenSeconds.value = Math.round((Date.now() - listenStartTime.value) / 1000)
    }
    phase.value = 'complete'
  } else {
    router.push('/learning-path')
  }
}

onMounted(() => {
  fetchMaterial()
})

onUnmounted(() => {
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.src = ''
  }
})
</script>

<template>
  <div class="content-card listening-page">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32"><Headset /></el-icon>
      <p>加载听力资料...</p>
    </div>

    <!-- 加载失败 -->
    <div v-else-if="materialError" class="error-state">
      <el-empty :description="materialError">
        <el-button @click="router.push('/learning-path')">返回学习路径</el-button>
      </el-empty>
    </div>

    <!-- 准备阶段 -->
    <div v-else-if="phase === 'ready'" class="phase-ready">
      <div class="ready-header">
        <el-button text @click="router.push('/learning-path')">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
      </div>

      <div class="ready-content">
        <div class="material-icon">
          <el-icon :size="48"><Headset /></el-icon>
        </div>
        <h2 class="material-title">{{ material?.title || '听力练习' }}</h2>
        <p class="material-desc" v-if="material?.description">{{ material.description }}</p>

        <div class="material-meta">
          <el-tag v-if="material?.cefr_level" type="warning" effect="plain">
            {{ material.cefr_level }}
          </el-tag>
          <el-tag v-if="material?.category" type="info" effect="plain">
            {{ material.category }}
          </el-tag>
          <span v-if="material?.duration_seconds" class="meta-duration">
            约 {{ Math.round(material.duration_seconds / 60) }} 分钟
          </span>
        </div>

        <el-button type="primary" size="large" @click="startListening" class="start-btn">
          <el-icon><VideoPlay /></el-icon>
          开始听力
        </el-button>
      </div>
    </div>

    <!-- 听力中阶段 -->
    <div v-else-if="phase === 'listening'" class="phase-listening">
      <div class="listening-header">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 结束听力
        </el-button>
        <span class="listening-title">{{ material?.title || '听力练习' }}</span>
      </div>

      <div class="player-card">
        <div class="player-visual">
          <div class="audio-wave" :class="{ playing: isPlaying }">
            <span v-for="i in 5" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.15}s` }"></span>
          </div>
        </div>

        <div class="player-controls">
          <div class="time-display">
            <span>{{ formattedCurrentTime }}</span>
            <div class="progress-bar" @click="(e) => {
              if (!audioRef) return
              const rect = e.target.getBoundingClientRect()
              const ratio = (e.clientX - rect.left) / rect.width
              audioRef.currentTime = ratio * audioDuration
            }">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <span>{{ formattedDuration }}</span>
          </div>

          <el-button
            type="primary"
            size="large"
            circle
            @click="togglePlay"
            class="play-btn"
          >
            <el-icon :size="28">
              <VideoPlay v-if="!isPlaying" />
              <VideoPause v-else />
            </el-icon>
          </el-button>

          <el-button
            type="success"
            @click="finishListening"
            :disabled="totalListenSeconds < 10 && !audioDuration"
          >
            <el-icon><CircleCheck /></el-icon>
            完成听力
          </el-button>
        </div>
      </div>

      <!-- 隐藏的音频元素 -->
      <audio
        ref="audioRef"
        :src="material?.url"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @play="onPlay"
        @pause="onPause"
        @ended="onEnded"
        preload="auto"
      ></audio>
    </div>

    <!-- 完成阶段 -->
    <div v-else-if="phase === 'complete'" class="phase-complete">
      <div class="complete-content">
        <div class="complete-icon">
          <el-icon :size="56" color="var(--color-success)"><CircleCheck /></el-icon>
        </div>
        <h2>听力练习完成</h2>
        <p class="complete-title">{{ material?.title || '听力练习' }}</p>
        <div class="complete-stats">
          <div class="stat-item">
            <span class="stat-label">听力时长</span>
            <span class="stat-value">{{ formattedListenTime }}</span>
          </div>
          <div class="stat-item" v-if="material?.cefr_level">
            <span class="stat-label">难度等级</span>
            <span class="stat-value">{{ material.cefr_level }}</span>
          </div>
        </div>

        <div class="complete-actions">
          <el-button @click="router.push('/learning-path')">返回学习路径</el-button>
          <el-button type="primary" @click="completeTask" :loading="completing">
            提交完成
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.listening-page {
  min-height: 60vh;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--color-text-secondary);
  gap: var(--spacing-md);
}

.error-state {
  padding: 40px 0;
}

// ========== 准备阶段 ==========
.phase-ready {
  .ready-header {
    margin-bottom: var(--spacing-xl);
  }

  .ready-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 40px 20px;
  }

  .material-icon {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background: rgba(var(--color-warning-rgb), 0.1);
    color: var(--color-warning);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: var(--spacing-xl);
  }

  .material-title {
    font-size: var(--font-size-xl);
    font-weight: 600;
    margin-bottom: var(--spacing-sm);
  }

  .material-desc {
    color: var(--color-text-secondary);
    max-width: 480px;
    margin-bottom: var(--spacing-lg);
    line-height: 1.6;
  }

  .material-meta {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-2xl);
    flex-wrap: wrap;
    justify-content: center;

    .meta-duration {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
    }
  }

  .start-btn {
    padding: 12px 40px;
    font-size: var(--font-size-lg);
  }
}

// ========== 听力中阶段 ==========
.phase-listening {
  .listening-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-2xl);

    .listening-title {
      font-weight: 600;
      font-size: var(--font-size-base);
      color: var(--color-text-secondary);
    }
  }

  .player-card {
    background: var(--color-bg-secondary);
    border-radius: var(--radius-xl);
    padding: 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-2xl);
  }

  .player-visual {
    padding: 30px 0;
  }

  .audio-wave {
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 60px;

    .wave-bar {
      width: 8px;
      height: 20px;
      background: var(--color-text-disabled);
      border-radius: 4px;
      transition: background 0.3s;
    }

    &.playing .wave-bar {
      background: var(--color-warning);
      animation: wave 0.8s ease-in-out infinite;
    }
  }

  @keyframes wave {
    0%, 100% { height: 20px; }
    50% { height: 60px; }
  }

  .player-controls {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-xl);
  }

  .time-display {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    font-variant-numeric: tabular-nums;
  }

  .progress-bar {
    flex: 1;
    height: 6px;
    background: var(--color-border);
    border-radius: 3px;
    cursor: pointer;
    overflow: hidden;

    .progress-fill {
      height: 100%;
      background: var(--color-warning);
      border-radius: 3px;
      transition: width 0.3s;
    }
  }

  .play-btn {
    width: 64px;
    height: 64px;
  }
}

// ========== 完成阶段 ==========
.phase-complete {
  .complete-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 40px 20px;
  }

  .complete-icon {
    margin-bottom: var(--spacing-lg);
  }

  h2 {
    font-size: var(--font-size-xl);
    font-weight: 600;
    margin-bottom: var(--spacing-sm);
  }

  .complete-title {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-xl);
  }

  .complete-stats {
    display: flex;
    gap: var(--spacing-2xl);
    margin-bottom: var(--spacing-2xl);
    padding: var(--spacing-lg) var(--spacing-2xl);
    background: var(--color-bg-secondary);
    border-radius: var(--radius-lg);
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-xs);

    .stat-label {
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }

    .stat-value {
      font-size: var(--font-size-lg);
      font-weight: 600;
    }
  }

  .complete-actions {
    display: flex;
    gap: var(--spacing-md);
  }
}
</style>