<script setup>
import { ref, onMounted } from 'vue'
import { useLearningPathStore } from '@/stores/learning_path'

const store = useLearningPathStore()

const refreshing = ref(false)
const lastUpdated = ref('')

async function refresh() {
  refreshing.value = true
  try {
    await store.fetchProfileSummary()
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  if (!store.profileSummary) {
    refresh()
  } else {
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
})
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <div>
        <h2 class="page-title">个人情况说明</h2>
        <p class="page-date">
          了解系统为什么推荐当前的学习路径和资料
          <span v-if="lastUpdated" class="update-time">· 更新于 {{ lastUpdated }}</span>
        </p>
      </div>
      <el-button :icon="'Refresh'" :loading="refreshing" @click="refresh" circle size="small" />
    </div>

    <div v-if="!store.profileSummary" class="summary-loading" v-loading="true">
      <p class="loading-hint">正在加载个人数据...</p>
    </div>

    <div v-else class="summary-content">
      <!-- 基础画像 -->
      <div class="summary-card">
        <div class="sc-header">
          <span class="sc-icon">📊</span> 个人学习画像
        </div>
        <div class="sc-body profile-grid">
          <div class="profile-item">
            <span class="pi-label">CEFR 等级</span>
            <el-tag type="primary" size="large">{{ store.profileSummary.cefr_level }}</el-tag>
          </div>
          <div class="profile-item">
            <span class="pi-label">等级来源</span>
            <span class="pi-value">{{ store.profileSummary.level_source }}</span>
          </div>
          <div class="profile-item">
            <span class="pi-label">学习目标</span>
            <span class="pi-value">{{ store.profileSummary.learning_goal }}</span>
          </div>
          <div class="profile-item">
            <span class="pi-label">年龄组</span>
            <span class="pi-value">{{ store.profileSummary.age_group }}</span>
          </div>
          <div class="profile-item profile-item--full">
            <span class="pi-label">兴趣偏好</span>
            <span class="pi-value">{{ store.profileSummary.interests?.join('、') || '未设置' }}</span>
          </div>
        </div>
      </div>

      <!-- 维度分数 -->
      <div class="summary-card">
        <div class="sc-header">
          <span class="sc-icon">📈</span> 维度能力分数
          <span class="sc-hint">（EMA 动态加权，近30天）</span>
        </div>
        <div class="sc-body">
          <div v-for="dim in store.profileSummary.dimension_scores" :key="dim.key" class="dimension-row">
            <div class="dr-header">
              <span class="dr-label">{{ dim.label }}</span>
              <span class="dr-score" :class="{ 'is-weakness': dim.is_weakness }">
                {{ dim.score !== null ? dim.score : '暂无数据' }}
              </span>
              <el-tag v-if="dim.is_weakness" type="danger" size="small">短板</el-tag>
            </div>
            <div class="dim-bar-bg">
              <div
                class="dim-bar-fill"
                :class="{ 'is-weakness': dim.is_weakness }"
                :style="{ width: (dim.score || 0) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 近期练习统计 -->
      <div class="summary-card">
        <div class="sc-header">
          <span class="sc-icon">📅</span> 近30天练习统计
        </div>
        <div class="sc-body stats-grid">
          <div class="stat-item">
            <span class="si-num">{{ store.profileSummary.recent_stats.total_tasks }}</span>
            <span class="si-label">总任务数</span>
          </div>
          <div class="stat-item">
            <span class="si-num">{{ store.profileSummary.recent_stats.completed_tasks }}</span>
            <span class="si-label">已完成</span>
          </div>
          <div class="stat-item">
            <span class="si-num">{{ store.profileSummary.recent_stats.pronunciation_count }}</span>
            <span class="si-label">发音练习</span>
            <span class="si-detail" v-if="store.profileSummary.recent_stats.avg_pronunciation_score">
              均分 {{ store.profileSummary.recent_stats.avg_pronunciation_score }}
            </span>
          </div>
          <div class="stat-item">
            <span class="si-num">{{ store.profileSummary.recent_stats.conversation_count }}</span>
            <span class="si-label">对话练习</span>
            <span class="si-detail" v-if="store.profileSummary.recent_stats.avg_conversation_score">
              均分 {{ store.profileSummary.recent_stats.avg_conversation_score }}
            </span>
          </div>
          <div class="stat-item">
            <span class="si-num">{{ store.profileSummary.recent_stats.roleplay_count }}</span>
            <span class="si-label">角色扮演</span>
          </div>
        </div>
      </div>

      <!-- 推荐算法说明 -->
      <div class="summary-card">
        <div class="sc-header">
          <span class="sc-icon">🧠</span> 推荐算法说明
          <el-tag type="info" size="small">{{ store.profileSummary.recommendation_logic.algorithm }}</el-tag>
        </div>
        <div class="sc-body">
          <div v-for="(factor, i) in store.profileSummary.recommendation_logic.factors" :key="i" class="factor-item">
            <div class="fi-header">
              <span class="fi-num">{{ i + 1 }}</span>
              <span class="fi-name">{{ factor.name }}</span>
              <el-tag size="small">{{ factor.weight }}</el-tag>
            </div>
            <p class="fi-desc">{{ factor.description }}</p>
          </div>
        </div>
      </div>
    </div>
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

  .update-time {
    color: var(--color-text-disabled);
  }
}

.summary-loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xxxl) 0;
}

.loading-hint {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.summary-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.sc-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-base);
  font-weight: 600;
}

.sc-icon {
  font-size: 18px;
}

.sc-body {
  padding: var(--spacing-xl);
}

.sc-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: 400;
  margin-left: auto;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.profile-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.profile-item--full {
  grid-column: 1 / -1;
}

.pi-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.pi-value {
  font-size: var(--font-size-base);
  font-weight: 500;
}

.dimension-row {
  margin-bottom: var(--spacing-lg);

  &:last-child { margin-bottom: 0; }
}

.dr-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.dr-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  width: 48px;
}

.dr-score {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-primary);

  &.is-weakness { color: var(--color-danger); }
}

.dim-bar-bg {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4px;
  transition: width 0.3s;

  &.is-weakness { background: var(--color-danger); }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--color-bg-primary);
  border-radius: var(--radius-md);
}

.si-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
}

.si-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.si-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.factor-item {
  padding: var(--spacing-md);
  background: var(--color-bg-primary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);

  &:last-child { margin-bottom: 0; }
}

.fi-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.fi-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: 600;
  flex-shrink: 0;
}

.fi-name {
  font-size: var(--font-size-base);
  font-weight: 600;
}

.fi-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}
</style>