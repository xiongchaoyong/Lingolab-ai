<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="home-page">
    <div class="welcome-section">
      <h2 class="page-title">
        欢迎回来，{{ authStore.userInfo?.username || '同学' }}
      </h2>
      <p class="welcome-subtitle">今日学习进度</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">0</div>
          <div class="stat-label">今日完成任务</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">0 分钟</div>
          <div class="stat-label">今日学习时长</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">0 天</div>
          <div class="stat-label">连续学习</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">--</div>
          <div class="stat-label">当前等级</div>
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
        <el-card shadow="hover" class="action-card" @click="$router.push('/learning-path')">
          <el-icon :size="36" color="#FDBA74"><Guide /></el-icon>
          <h4>学习路径</h4>
          <p>个性化每日任务，系统提升英语水平</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.home-page {
  .welcome-section {
    margin-bottom: var(--spacing-xl);

    .welcome-subtitle {
      color: var(--color-text-secondary);
      font-family: var(--font-body);
    }
  }

  .stats-row {
    margin-bottom: var(--spacing-xxl);
  }

  .stat-card {
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-base);

    &:hover {
      transform: translateY(-2px);
    }

    .stat-value {
      font-family: var(--font-heading);
      font-size: 28px;
      font-weight: 700;
      color: var(--color-primary);
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
</style>
