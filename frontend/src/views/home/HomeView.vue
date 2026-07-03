<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProgressStore } from '@/stores/progress'

const authStore = useAuthStore()
const progressStore = useProgressStore()
const loading = ref(true)

const levelLabel = computed(() => {
  const level = authStore.userInfo?.level_final
  if (!level) return null
  const map = { A1: '入门', A2: '基础', B1: '进阶', B2: '中高级', C1: '流利', C2: '精通' }
  return `${level} · ${map[level] || ''}`
})

onMounted(async () => {
  await progressStore.fetchAll()
  loading.value = false
})
</script>

<template>
  <div class="home-page">
    <div class="welcome-section">
      <el-avatar :size="48" :src="authStore.userInfo?.avatar" icon="UserFilled" class="welcome-avatar" />
      <div>
        <h2 class="page-title">
          欢迎回来，{{ authStore.userInfo?.username || '同学' }}
        </h2>
        <p class="welcome-subtitle">
          <template v-if="levelLabel">当前等级：{{ levelLabel }}</template>
          <template v-else>今日学习进度</template>
        </p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row v-loading="loading" :gutter="16" class="stats-row">
      <el-col v-for="stat in progressStore.statCards" :key="stat.label" :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stat.value }}<small>{{ stat.unit }}</small></div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <h3 class="section-title">开始练习</h3>
    <el-row :gutter="16" class="quick-actions">
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/pronunciation')">
          <el-icon :size="36" color="#A78BFA"><Microphone /></el-icon>
          <h4>发音评测</h4>
          <p>跟读标准发音，获取多维度评分</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/conversation')">
          <el-icon :size="36" color="#C4B5FD"><ChatDotRound /></el-icon>
          <h4>AI 对话</h4>
          <p>沉浸式场景对话，提升口语流利度</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/progress')">
          <el-icon :size="36" color="#FDBA74"><DataAnalysis /></el-icon>
          <h4>学习报告</h4>
          <p>查看详细学习数据与趋势分析</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.home-page {
  .welcome-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);

    .welcome-avatar {
      flex-shrink: 0;
    }

    .page-title {
      font-family: var(--font-heading);
      font-size: var(--font-size-xl);
      font-weight: 700;
      margin: 0;
    }

    .welcome-subtitle {
      margin-top: 4px;
      color: var(--color-text-secondary);
      font-family: var(--font-body);
    }
  }

  .stats-row {
    margin-bottom: var(--spacing-xxl);
  }

  .stat-card {
    text-align: center;
    transition: all var(--transition-base);
    margin-bottom: var(--spacing-base);

    &:hover {
      transform: translateY(-2px);
    }

    .stat-value {
      font-family: var(--font-heading);
      font-size: 24px;
      font-weight: 700;
      color: var(--color-primary);
      small {
        font-size: 14px;
        font-weight: 400;
        color: var(--color-text-secondary);
        margin-left: 2px;
      }
    }

    .stat-label {
      margin-top: var(--spacing-xs);
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
      font-family: var(--font-body);
    }
  }

  .section-title {
    font-family: var(--font-heading);
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin-bottom: var(--spacing-base);
  }

  .quick-actions {
    .action-card {
      cursor: pointer;
      text-align: center;
      padding: var(--spacing-xl) var(--spacing-base);
      transition: all var(--transition-base);

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
      }

      h4 {
        font-family: var(--font-heading);
        margin: var(--spacing-md) 0 var(--spacing-sm);
        font-size: var(--font-size-base);
      }

      p {
        color: var(--color-text-secondary);
        font-family: var(--font-body);
        font-size: var(--font-size-sm);
      }
    }
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .home-page .stats-row .stat-value {
    font-size: 18px;
  }
}
</style>
