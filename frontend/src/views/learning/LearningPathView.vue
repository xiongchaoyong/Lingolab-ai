<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Mock 今日任务
const todayTasks = ref([
  {
    id: 1, type: 'shadowing', icon: 'Microphone', title: '跟读练习',
    duration: '5-10分钟', difficulty: 'B1',
    desc: '5 个句子跟读，聚焦 /θ/ /ð/ 音素发音',
    tag: '短板音素练习', status: 'done',
    completedAt: '2分钟前',
  },
  {
    id: 2, type: 'conversation', icon: 'ChatDotRound', title: '情景对话',
    duration: '10-15分钟', difficulty: 'B1',
    desc: '场景：餐厅点餐 · 5 轮 AI 对话',
    tag: '日常交流场景', status: 'pending',
  },
  {
    id: 3, type: 'listening', icon: 'Headset', title: '听力训练',
    duration: '5分钟', difficulty: 'A2',
    desc: '1 段短对话 + 2 道听力理解题',
    tag: '对话理解', status: 'pending',
  },
])

// 模拟历史记录
const historyRecords = ref([
  { date: '6月2日', tasks: ['done', 'done', 'skipped'], completed: 2, total: 3, minutes: 22 },
  { date: '6月1日', tasks: ['done', 'done', 'done'], completed: 3, total: 3, minutes: 28 },
  { date: '5月31日', tasks: ['done', 'skipped', 'done'], completed: 2, total: 3, minutes: 18 },
  { date: '5月30日', tasks: ['done', 'done', 'done'], completed: 3, total: 3, minutes: 30 },
])

const todayProgress = computed(() => {
  const done = todayTasks.value.filter(t => t.status === 'done').length
  return { done, total: todayTasks.value.length }
})

function getStatusIcon(status) {
  if (status === 'done') return 'CircleCheckFilled'
  if (status === 'skipped') return 'RemoveFilled'
  return 'Clock'
}

function getStatusColor(status) {
  if (status === 'done') return 'var(--color-success)'
  if (status === 'skipped') return 'var(--color-text-disabled)'
  return 'var(--color-warning)'
}

function startTask(task) {
  if (task.type === 'conversation') router.push('/conversation')
  else if (task.type === 'shadowing') router.push('/pronunciation')
  // listening → placeholder
}

function skipTask(task) {
  task.status = 'skipped'
}

function replaceTask(task) {
  task.desc = '已更换为新内容（模拟换一批）'
  task.status = 'pending'
}

function adjustDifficulty(task) {
  const levels = ['A1', 'A2', 'B1', 'B2', 'C1']
  const idx = levels.indexOf(task.difficulty)
  task.difficulty = levels[Math.min(idx + 1, levels.length - 1)]
}
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
        :percentage="Math.round((todayProgress.done / todayProgress.total) * 100)"
        :stroke-width="8"
        :show-text="false"
        style="width: 120px"
        color="var(--color-primary)"
      />
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <div
        v-for="task in todayTasks"
        :key="task.id"
        class="task-card"
        :class="{ 'is-completed': task.status === 'done', 'is-skipped': task.status === 'skipped' }"
      >
        <div class="task-left">
          <div class="task-icon" :class="task.type">
            <el-icon :size="24"><component :is="task.icon" /></el-icon>
          </div>
        </div>

        <div class="task-body">
          <div class="task-header">
            <h4>{{ task.title }}</h4>
            <el-tag size="small" effect="plain" :type="task.difficulty === 'B1' ? 'warning' : 'success'">
              {{ task.difficulty }}
            </el-tag>
            <el-tag size="small" effect="plain" type="info">{{ task.tag }}</el-tag>
            <span class="task-duration">{{ task.duration }}</span>
          </div>
          <p class="task-desc">{{ task.desc }}</p>

          <!-- 未完成操作 -->
          <div v-if="task.status === 'pending'" class="task-actions">
            <el-button text size="small" @click="skipTask(task)">跳过</el-button>
            <el-button text size="small" @click="replaceTask(task)">换一个</el-button>
            <el-dropdown @command="adjustDifficulty(task)">
              <el-button text size="small">
                调整难度 <el-icon><ArrowDown /></el-icon>
              </el-button>
            </el-dropdown>
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
              {{ task.status === 'done' ? `已完成 (${task.completedAt})` : '已跳过' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <el-collapse class="history-collapse">
      <el-collapse-item title="历史记录（最近 7 天）">
        <div class="history-list">
          <div v-for="record in historyRecords" :key="record.date" class="history-row">
            <span class="history-date">{{ record.date }}</span>
            <span class="history-indicators">
              <span
                v-for="(s, i) in record.tasks"
                :key="i"
                class="history-dot"
                :class="{ done: s === 'done', skipped: s === 'skipped', pending: s === 'pending' }"
              >
                {{ s === 'done' ? '✓' : s === 'skipped' ? '✗' : '○' }}
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
