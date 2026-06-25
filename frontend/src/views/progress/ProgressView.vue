<script setup>
import { computed, onMounted } from 'vue'
import { useProgressStore } from '@/stores/progress'
import { usePredictionStore } from '@/stores/prediction'

const store = useProgressStore()
const predStore = usePredictionStore()

const predDisplay = computed(() => {
  const p = predStore.prediction
  return {
    currentScore: p.current_score ?? 0,
    trendSlope: p.trend_slope != null ? `+${p.trend_slope}` : '--',
    trend: p.trend || 'stable',
    predictedDate: p.predicted_date || '--',
    predictedDays: p.predicted_days != null ? `${p.predicted_days} 天` : '--',
    targetScore: p.target_score ?? 85,
    predNote:
      p.predicted_days != null
        ? `按当前节奏，距离目标 ${p.target_score} 分还需 ${p.predicted_days} 天`
        : p.message || '数据不足，继续学习 3 天后再查看预测',
  }
})

onMounted(() => {
  store.fetchAll('week')
  predStore.fetchPrediction()
  predStore.checkAlerts()
})
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <h2 class="page-title">学习报告</h2>
      <el-radio-group v-model="store.timeRange" size="small" @change="store.setTimeRange">
        <el-radio-button value="day">天</el-radio-button>
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
        <el-radio-button value="all">全部</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载中 -->
    <div v-if="store.loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="store.isEmpty" class="empty-state">
      <el-empty description="暂无学习数据">
        <template #image>
          <el-icon :size="64" color="var(--color-text-disabled)"><DataLine /></el-icon>
        </template>
        <p class="empty-hint">完成首次测评和练习后，这里会展示你的学习进步轨迹</p>
        <el-button type="primary" @click="$router.push('/assessment')">去完成测评</el-button>
      </el-empty>
    </div>

    <template v-else>
      <!-- 图表区 -->
      <el-row :gutter="16" class="charts-row">
        <el-col :span="12">
          <div class="chart-box">
            <h4 class="chart-title">能力雷达图</h4>
            <v-chart v-if="store.radarData.dimensions?.length" :option="store.radarOption" autoresize style="height: 320px" />
            <el-empty v-else description="暂无雷达图数据" :image-size="60" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-box">
            <h4 class="chart-title">趋势折线图</h4>
            <v-chart v-if="store.trendData.points?.length" :option="store.lineOption" autoresize style="height: 320px" />
            <el-empty v-else description="暂无趋势数据" :image-size="60" />
          </div>
        </el-col>
      </el-row>

      <!-- 日历热力图 -->
      <div class="chart-box" style="margin-top: var(--spacing-lg);">
        <h4 class="chart-title">学习日历</h4>
        <v-chart v-if="store.heatmapData.days?.length" :option="store.calendarOption" autoresize style="height: 200px" />
        <el-empty v-else description="暂无日历数据" :image-size="60" />
      </div>

      <!-- 学习预测（4.3 接入真实 API） -->
      <div class="chart-box" style="margin-top: var(--spacing-lg);">
        <h4 class="chart-title">学习预测</h4>
        <div class="prediction-content">
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">当前综合分</span>
                <span class="pred-value">{{ predDisplay.currentScore }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">趋势</span>
                <span class="pred-value" :style="{ color: predDisplay.trend === 'up' ? 'var(--color-success)' : 'var(--color-danger)' }">
                  {{ predDisplay.trendSlope }} 分/天
                </span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">预计达标</span>
                <span class="pred-value">{{ predDisplay.predictedDate }}（{{ predDisplay.predictedDays }}）</span>
              </div>
            </el-col>
          </el-row>
          <div class="pred-note">{{ predDisplay.predNote }}</div>
        </div>
      </div>

      <!-- 预警通知（4.3 接入真实 API） -->
      <div class="chart-box" style="margin-top: var(--spacing-base);" v-if="predStore.alerts.length">
        <h4 class="chart-title">系统提醒</h4>
        <div v-for="alert in predStore.alerts" :key="alert.type" class="alert-item">
          <el-icon color="var(--color-warning)"><WarningFilled /></el-icon>
          <span>{{ alert.message }}</span>
        </div>
      </div>

      <!-- 统计卡片 -->
      <h4 class="chart-title" style="margin-top: var(--spacing-xl);">学习统计</h4>
      <el-row :gutter="12">
        <el-col :span="4" v-for="card in store.statCards" :key="card.label">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-unit">{{ card.unit }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.loading-state { min-height: 300px; }

.empty-state {
  padding: var(--spacing-huge) 0;
  text-align: center;

  .empty-hint {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-lg);
  }
}

.charts-row { margin-bottom: 0; }

.chart-box {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
}

.chart-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.prediction-content { padding: var(--spacing-md) 0; }
.pred-item {
  text-align: center; padding: var(--spacing-md);
  background: var(--color-bg-secondary); border-radius: var(--radius-sm);
  .pred-label { display: block; color: var(--color-text-secondary); font-size: var(--font-size-sm); margin-bottom: var(--spacing-xs); }
  .pred-value { display: block; font-size: var(--font-size-lg); font-weight: 700; color: var(--color-text-primary); }
}
.pred-note {
  margin-top: var(--spacing-lg); padding: var(--spacing-md); text-align: center;
  background: rgba(var(--color-primary-rgb), 0.05); border-radius: var(--radius-sm);
  color: var(--color-primary); font-weight: 500;
}
.alert-item {
  display: flex; align-items: center; gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md); color: var(--color-text-secondary); font-size: var(--font-size-sm);
}

.stat-card {
  text-align: center;
  margin-top: var(--spacing-base);

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-primary);
  }

  .stat-unit {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .stat-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-disabled);
  }
}
</style>