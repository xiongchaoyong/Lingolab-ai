<script setup>
import { ref, computed, onMounted } from 'vue'

const timeRange = ref('week')

// ========== Mock 数据 ==========

// 雷达图数据
const radarData = {
  dimensions: ['发音准确率', '流利度', '语法', '听力', '表达丰富度'],
  current: [72, 65, 78, 80, 60],
  previous: [65, 58, 75, 75, 55],
}

// 趋势折线图数据
const trendData = {
  week: {
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    pronunciation: [68, 70, 72, 71, 74, 73, 72],
    fluency: [60, 62, 63, 64, 65, 66, 65],
  },
  month: {
    labels: ['W1', 'W2', 'W3', 'W4'],
    pronunciation: [65, 69, 72, 73],
    fluency: [58, 62, 64, 65],
  },
  all: {
    labels: ['5月', '6月'],
    pronunciation: [60, 72],
    fluency: [55, 65],
  },
}

// 统计指标
const stats = ref({
  totalMinutes: 720,
  checkinDays: 23,
  streakDays: 7,
  maxStreak: 14,
  shadowCount: 45,
  conversationCount: 18,
})

// ========== ECharts 配置 ==========

const radarOption = computed(() => ({
  tooltip: {},
  legend: { data: ['当前', '上次'], bottom: 0 },
  radar: {
    indicator: radarData.dimensions.map(d => ({ name: d, max: 100 })),
    center: ['50%', '55%'],
  },
  series: [{
    type: 'radar',
    data: [
      { value: radarData.current, name: '当前', lineStyle: { color: '#A78BFA' }, areaStyle: { color: 'rgba(167,139,250,0.15)' } },
      { value: radarData.previous, name: '上次', lineStyle: { color: '#C4B5D4', type: 'dashed' }, areaStyle: { color: 'rgba(196,181,212,0.12)' } },
    ],
  }],
}))

const lineOption = computed(() => {
  const data = trendData[timeRange.value]
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['发音准确率', '流利度'], bottom: 0 },
    grid: { left: 8, right: 8, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: data.labels },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [
      { name: '发音准确率', type: 'line', data: data.pronunciation, smooth: true, lineStyle: { color: '#A78BFA' }, itemStyle: { color: '#A78BFA' } },
      { name: '流利度', type: 'line', data: data.fluency, smooth: true, lineStyle: { color: '#C4B5FD' }, itemStyle: { color: '#C4B5FD' } },
    ],
  }
})

// 日历热力图数据（简化）
const calendarOption = computed(() => {
  const now = new Date()
  const data = []
  for (let i = 180; i >= 0; i--) {
    const d = new Date(now - i * 86400000)
    const val = Math.random() > 0.3 ? Math.floor(Math.random() * 4) : 0
    data.push([d.toISOString().slice(0, 10), val])
  }
  return {
    tooltip: {},
    visualMap: {
      min: 0, max: 3,
      orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#E2E8F0', '#A7F3D0', '#6EE7B7', '#059669'] },
      textStyle: { color: '#64748B' },
    },
    calendar: {
      range: '2026',
      cellSize: ['auto', 14],
      dayLabel: { nameMap: ['日', '一', '二', '三', '四', '五', '六'] },
      monthLabel: { nameMap: 'cn' },
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data,
    }],
  }
})

const statCards = computed(() => [
  { label: '累计学习', value: `${Math.floor(stats.value.totalMinutes / 60)}h`, unit: `${stats.value.totalMinutes}min` },
  { label: '累计打卡', value: stats.value.checkinDays, unit: '天' },
  { label: '连续打卡', value: stats.value.streakDays, unit: '天' },
  { label: '最长连续', value: stats.value.maxStreak, unit: '天' },
  { label: '跟读次数', value: stats.value.shadowCount, unit: '次' },
  { label: '对话次数', value: stats.value.conversationCount, unit: '次' },
])

// ========== 预测数据 ==========
const prediction = ref({
  currentScore: 72,
  trendSlope: 0.35,
  targetScore: 85,
  predictedDays: 37,
  predictedDate: '7月5日',
  trend: 'up',
})

const alerts = ref([
  { id: 1, level: 'info', msg: '连续打卡 7 天，继续保持！' },
])

// 空状态(暂不使用, 保留)
const isEmpty = ref(false)
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <h2 class="page-title">学习报告</h2>
      <el-radio-group v-model="timeRange" size="small">
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
        <el-radio-button value="all">全部</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 空状态 -->
    <div v-if="isEmpty" class="empty-state">
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
            <v-chart :option="radarOption" autoresize style="height: 320px" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-box">
            <h4 class="chart-title">趋势折线图</h4>
            <v-chart :option="lineOption" autoresize style="height: 320px" />
          </div>
        </el-col>
      </el-row>

      <!-- 日历热力图 -->
      <div class="chart-box" style="margin-top: var(--spacing-lg);">
        <h4 class="chart-title">学习日历</h4>
        <v-chart :option="calendarOption" autoresize style="height: 200px" />
      </div>

      <!-- 学习预测 -->
      <div class="chart-box" style="margin-top: var(--spacing-lg);">
        <h4 class="chart-title">学习预测</h4>
        <div class="prediction-content">
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">当前综合分</span>
                <span class="pred-value">{{ prediction.currentScore }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">趋势</span>
                <span class="pred-value" :style="{ color: prediction.trend === 'up' ? 'var(--color-success)' : 'var(--color-danger)' }">
                  +{{ prediction.trendSlope }} 分/天
                </span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pred-item">
                <span class="pred-label">预计达标</span>
                <span class="pred-value">{{ prediction.predictedDate }}（{{ prediction.predictedDays }} 天）</span>
              </div>
            </el-col>
          </el-row>
          <div class="pred-note">按当前节奏，距离目标 {{ prediction.targetScore }} 分还需 {{ prediction.predictedDays }} 天</div>
        </div>
      </div>

      <!-- 预警通知 -->
      <div class="chart-box" style="margin-top: var(--spacing-base);" v-if="alerts.length">
        <h4 class="chart-title">系统提醒</h4>
        <div v-for="alert in alerts" :key="alert.id" class="alert-item">
          <el-icon color="var(--color-warning)"><WarningFilled /></el-icon>
          <span>{{ alert.msg }}</span>
        </div>
      </div>

      <!-- 统计卡片 -->
      <h4 class="chart-title" style="margin-top: var(--spacing-xl);">学习统计</h4>
      <el-row :gutter="12">
        <el-col :span="4" v-for="card in statCards" :key="card.label">
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

.empty-state {
  padding: var(--spacing-huge) 0;
  text-align: center;

  .empty-hint {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-lg);
  }
}

.charts-row {
  margin-bottom: 0;
}

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
