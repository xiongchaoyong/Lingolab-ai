<script setup>
import { ref, onMounted } from 'vue'
import { usePredictionStore } from '@/stores/prediction'
import { ElMessage } from 'element-plus'

const store = usePredictionStore()
const loading = ref(false)

onMounted(() => { loadNotices() })

async function loadNotices() {
  loading.value = true
  try {
    await store.fetchNotices()
  } catch {
    ElMessage.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

async function handleMarkRead(notice) {
  if (notice.is_read) return
  try {
    await store.markRead(notice.id)
    notice.is_read = true
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleMarkAll() {
  try {
    await store.markAllRead()
    store.notices.forEach(n => { n.is_read = true })
    ElMessage.success('已全部标记为已读')
  } catch {
    ElMessage.error('操作失败')
  }
}

function getLevelTag(level) {
  return level === 'warning' ? 'warning' : 'info'
}

function getTypeLabel(type) {
  const map = { prediction: '学习预测', alert: '预警提醒', achievement: '成就通知' }
  return map[type] || type
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">通知中心</h2>
      <el-button
        v-if="store.unreadCount > 0"
        text type="primary"
        @click="handleMarkAll"
      >
        全部已读
      </el-button>
    </div>

    <div v-loading="loading">
      <template v-if="store.notices.length > 0">
        <div
          v-for="notice in store.notices"
          :key="notice.id"
          :class="['notice-item', { unread: !notice.is_read }]"
          @click="handleMarkRead(notice)"
        >
          <div class="notice-header">
            <el-tag size="small" :type="getLevelTag(notice.level)">
              {{ getTypeLabel(notice.type) }}
            </el-tag>
            <span class="notice-time">{{ notice.created_at?.slice(0, 16).replace('T', ' ') }}</span>
          </div>
          <h4 class="notice-title">{{ notice.title }}</h4>
          <p class="notice-message">{{ notice.message }}</p>
          <el-icon v-if="!notice.is_read" class="unread-dot"><CircleCheckFilled /></el-icon>
        </div>
      </template>
      <el-empty v-else description="暂无通知" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.notice-item {
  position: relative;
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  border-bottom: 1px solid var(--color-border-light);

  &:hover { background: rgba(var(--color-primary-rgb), 0.03); }
  &.unread { background: rgba(var(--color-primary-rgb), 0.05); }
}

.notice-header {
  display: flex; align-items: center; gap: var(--spacing-sm); margin-bottom: var(--spacing-xs);
}

.notice-time {
  font-size: var(--font-size-xs); color: var(--color-text-disabled);
}

.notice-title {
  font-size: var(--font-size-base); font-weight: 600; margin: 0 0 var(--spacing-xs) 0;
  color: var(--color-text-primary);
}

.notice-message {
  margin: 0; font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 1.5;
}

.unread-dot {
  position: absolute; top: var(--spacing-lg); right: var(--spacing-lg);
  color: var(--color-primary); font-size: 10px;
}
</style>