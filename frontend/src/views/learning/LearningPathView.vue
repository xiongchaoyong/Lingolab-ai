<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLearningPathStore } from '@/stores/learning_path'

const router = useRouter()
const store = useLearningPathStore()

const historyExpanded = ref(false)

const todayProgress = computed(() => store.progress)

function getStatusIcon(status) {
  if (status === 'completed') return 'CircleCheckFilled'
  if (status === 'skipped') return 'RemoveFilled'
  return 'Clock'
}

function getStatusColor(status) {
  if (status === 'completed') return 'var(--color-success)'
  if (status === 'skipped') return 'var(--color-text-disabled)'
  return 'var(--color-warning)'
}

function getStatusLabel(status) {
  if (status === 'completed') return '已完成'
  if (status === 'skipped') return '已跳过'
  return '待开始'
}

function getTypeIcon(type) {
  if (type === 'shadowing') return 'Microphone'
  if (type === 'conversation') return 'ChatDotRound'
  return 'Headset'
}

function startTask(task) {
  if (task.type === 'conversation') router.push('/conversation')
  else if (task.type === 'shadowing') router.push('/pronunciation')
  else if (task.type === 'listening') router.push(`/listening?taskId=${task.id}`)
}

async function skipTask(task) {
  await store.skipTask(task.id)
}

async function replaceTask(task) {
  await store.replaceTask(task.id)
}

async function adjustDifficulty(task) {
  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
  const idx = levels.indexOf(task.difficulty)
  const direction = idx < levels.length - 1 ? 'harder' : 'easier'
  await store.adjustDifficulty(task.id, direction)
}

async function toggleHistory() {
  historyExpanded.value = !historyExpanded.value
  if (historyExpanded.value && store.historyRecords.length === 0) {
    await store.fetchHistory()
  }
}

onMounted(() => {
  store.fetchDailyTasks()
})
</script>

<template>
  <div class="content-card">
    <!-- 头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">今日学习任务</h2>
        <p class="page-date">已完成 {{ todayProgress.done }} / {{ todayProgress.total }} 个任务</p>
      </div>
      <el-progress
        :percentage="todayProgress.total > 0 ? Math.round((todayProgress.done / todayProgress.total) * 100) : 0"
        :stroke-width="8"
        :show-text="false"
        style="width: 120px"
        color="var(--color-primary)"
      />
    </div>

    <!-- 任务列表 -->
    <div class="task-list" v-loading="store.loading">
      <div
        v-for="task in store.tasks"
        :key="task.id"
        class="task-card"
        :class="{ 'is-completed': task.status === 'completed', 'is-skipped': task.status === 'skipped' }"
      >
        <div class="task-left">
          <div class="task-icon" :class="task.type">
            <el-icon :size="24"><component :is="getTypeIcon(task.type)" /></el-icon>
          </div>
        </div>

        <div class="task-body">
          <div class="task-header">
            <h4>{{ task.title }}</h4>
            <el-tag size="small" effect="plain" :type="task.difficulty === 'B1' ? 'warning' : 'success'">
              {{ task.difficulty }}
            </el-tag>
            <el-tag v-if="task.tag" size="small" effect="plain" type="info">{{ task.tag }}</el-tag>
            <span class="task-duration">{{ task.duration }}</span>
          </div>
          <p class="task-desc">{{ task.description }}</p>

          <!-- 未完成操作 -->
          <div v-if="task.status === 'pending'" class="task-actions">
            <el-button text size="small" @click="skipTask(task)">跳过</el-button>
            <el-button text size="small" @click="replaceTask(task)">换一个</el-button>
            <el-button text size="small" @click="adjustDifficulty(task)">调整难度</el-button>
            <el-button type="primary" size="small" @click="startTask(task)">
              {{ task.type === 'conversation' ? '开始对话' : task.type === 'shadowing' ? '开始跟读' : '开始听力' }}
            </el-button>
          </div>

          <!-- 已完成 / 已跳过 -->
          <div v-else class="task-status-label">
            <el-icon :size="16" :color="getStatusColor(task.status)">
              <component :is="getStatusIcon(task.status)" />
            </el-icon>
            <span :style="{ color: getStatusColor(task.status) }">
              {{ getStatusLabel(task.status) }}
            </span>
          </div>
        </div>
      </div>

      <el-empty v-if="!store.loading && store.tasks.length === 0" description="暂无任务" />
    </div>

    <!-- 历史记录 -->
    <el-collapse class="history-collapse" v-model="historyExpanded">
      <el-collapse-item title="历史记录（最近 7 天）" name="history" @click.prevent="toggleHistory">
        <div class="history-list" v-loading="store.loading">
          <div v-for="record in store.historyRecords" :key="record.date" class="history-row">
            <span class="history-date">{{ record.date }}</span>
            <span class="history-indicators">
              <span
                v-for="(s, i) in record.tasks"
                :key="i"
                class="history-dot"
                :class="{ done: s === 'completed', skipped: s === 'skipped', pending: s === 'pending' }"
              >
                {{ s === 'completed' ? '✓' : s === 'skipped' ? '✗' : '○' }}
              </span>
            </span>
            <span class="history-stat">完成 {{ record.completed }}/{{ record.total }}</span>
            <span class="history-time">{{ record.minutes }} 分钟</span>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style lang="scss" scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);

  .page-date {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    margin-top: var(--spacing-xs);
  }
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.task-card {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all 0.2s;

  &.is-completed {
    border-color: var(--color-success);
    background: rgba(var(--color-success-rgb), 0.03);
  }

  &.is-skipped {
    opacity: 0.6;
  }
}

.task-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;

  &.shadowing { background: rgba(var(--color-primary-rgb), 0.1); color: var(--color-primary); }
  &.conversation { background: rgba(var(--color-success-rgb), 0.1); color: var(--color-success); }
  &.listening { background: rgba(var(--color-warning-rgb), 0.1); color: var(--color-warning); }
}

.task-body {
  flex: 1;
}

.task-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-sm);

  h4 {
    font-size: var(--font-size-base);
    font-weight: 600;
  }

  .task-duration {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-left: auto;
  }
}

.task-desc {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-md);
}

.task-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.task-status-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
}

// 历史记录
.history-collapse {
  background: transparent;
  border: none;

  :deep(.el-collapse-item__header) {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    border: none;
  }

  :deep(.el-collapse-item__wrap) {
    border: none;
  }
}

.history-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);

  &:last-child { border-bottom: none; }
}

.history-date {
  color: var(--color-text-primary);
  font-weight: 500;
  width: 80px;
}

.history-indicators {
  display: flex;
  gap: var(--spacing-xs);
}

.history-dot {
  &.done { color: var(--color-success); }
  &.skipped { color: var(--color-text-disabled); }
  &.pending { color: var(--color-warning); }
}

.history-stat, .history-time {
  color: var(--color-text-secondary);
}
</style>
