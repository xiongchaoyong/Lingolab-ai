<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

const store = useAdminStore()
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await store.fetchDashboard()
  } finally {
    loading.value = false
  }
})

const d = computed(() => store.dashboard?.metrics || {})

const metricGroups = computed(() => [
  {
    label: '用户规模',
    items: [
      { label: '总用户', value: String(d.value.total_users || 0), color: '#A78BFA' },
      { label: '活跃用户', value: String(d.value.active_users || 0), color: '#C4B5FD' },
      { label: '日新增', value: String(d.value.daily_new_users || 0), color: '#FDE68A' },
      { label: '日活(DAU)', value: String(d.value.dau || 0), color: '#93C5FD' },
      { label: '月活(MAU)', value: String(d.value.mau || 0), color: '#86EFAC' },
    ],
  },
  {
    label: '学习活跃',
    items: [
      { label: '今日对话', value: String(d.value.today_conversations || 0), color: '#60A5FA' },
      { label: '今日发音', value: String(d.value.today_pronunciation || 0), color: '#34D399' },
      { label: '今日任务完成', value: String(d.value.today_tasks_completed || 0), color: '#FBBF24' },
      { label: '任务完成率', value: d.value.task_completion_rate != null ? d.value.task_completion_rate + '%' : '-', color: '#F472B6' },
      { label: '对话完成率', value: d.value.conversation_completion_rate != null ? d.value.conversation_completion_rate + '%' : '-', color: '#818CF8' },
    ],
  },
  {
    label: '运营概况',
    items: [
      { label: '老师数', value: String(d.value.teacher_count || 0), color: '#7C3AED' },
      { label: '班级数', value: String(d.value.total_classes || 0), color: '#8B5CF6' },
      { label: '班均学生', value: d.value.avg_students_per_class != null ? String(d.value.avg_students_per_class) : '-', color: '#A78BFA' },
      { label: '总积分', value: formatNumber(d.value.total_points || 0), color: '#F59E0B' },
      { label: '总时长(h)', value: d.value.total_duration_minutes ? String(Math.floor(d.value.total_duration_minutes / 60)) : '0', color: '#EC4899' },
    ],
  },
])

function formatNumber(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

const dailyActivityOption = computed(() => {
  const data = store.dashboard?.daily_activity || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: data.map(t => t.label) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      name: 'DAU', type: 'line', smooth: true,
      data: data.map(t => t.value),
      areaStyle: { color: 'rgba(96,165,250,0.12)' },
      lineStyle: { color: '#60A5FA' },
      itemStyle: { color: '#60A5FA' },
    }],
  }
})

const lineOption = computed(() => {
  const trend = store.dashboard?.user_trend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: trend.map(t => t.label) },
    yAxis: { type: 'value' },
    series: [{
      name: '新增用户', type: 'line', smooth: true,
      data: trend.map(t => t.value),
      areaStyle: { color: 'rgba(167,139,250,0.12)' },
      lineStyle: { color: '#A78BFA' },
    }],
  }
})

const pieOption = computed(() => {
  const dist = store.dashboard?.level_distribution || {}
  const data = Object.entries(dist).map(([name, value]) => ({ name, value }))
  return {
    tooltip: {},
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
      data,
      label: { show: false },
    }],
  }
})

const typeBarOption = computed(() => {
  const dist = store.dashboard?.content_type_distribution || {}
  const data = Object.entries(dist).map(([name, value]) => ({ name, value }))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: data.map(d => d.name) },
    yAxis: { type: 'value' },
    series: [{
      name: '练习次数', type: 'bar',
      data: data.map(d => d.value),
      itemStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#A78BFA' },
            { offset: 1, color: '#C4B5FD' },
          ],
        },
        borderRadius: [6, 6, 0, 0],
      },
    }],
  }
})
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">运营数据看板</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" style="text-align:center;padding:60px 0;">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <template v-else-if="store.dashboard">
      <!-- 分组指标卡片 -->
      <div v-for="group in metricGroups" :key="group.label" class="metrics-section">
        <h4 class="section-label">{{ group.label }}</h4>
        <el-row :gutter="16" class="metrics-row">
          <el-col :span="4" v-for="m in group.items" :key="m.label" style="margin-bottom: var(--spacing-base);">
            <div class="metric-card" :style="{ borderTopColor: m.color }">
              <div class="metric-value" :style="{ color: m.color }">{{ m.value }}</div>
              <div class="metric-label">{{ m.label }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 图表行1：7日DAU + CEFR分布 -->
      <el-row :gutter="16" style="margin-top: var(--spacing-lg);">
        <el-col :span="14">
          <div class="chart-box">
            <h4 class="chart-title">近7日 日活趋势</h4>
            <v-chart :option="dailyActivityOption" autoresize style="height: 300px" />
          </div>
        </el-col>
        <el-col :span="10">
          <div class="chart-box">
            <h4 class="chart-title">CEFR 等级分布</h4>
            <v-chart :option="pieOption" autoresize style="height: 300px" />
          </div>
        </el-col>
      </el-row>

      <!-- 图表行2：用户增长 + 练习类型 -->
      <el-row :gutter="16" style="margin-top: var(--spacing-lg);">
        <el-col :span="14">
          <div class="chart-box">
            <h4 class="chart-title">用户增长趋势（近6月）</h4>
            <v-chart :option="lineOption" autoresize style="height: 300px" />
          </div>
        </el-col>
        <el-col :span="10">
          <div class="chart-box">
            <h4 class="chart-title">练习类型分布</h4>
            <v-chart :option="typeBarOption" autoresize style="height: 300px" />
          </div>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="暂无数据" />
  </div>
</template>

<style lang="scss" scoped>
.metrics-section {
  margin-bottom: var(--spacing-sm);

  .section-label {
    font-size: var(--font-size-sm);
    font-weight: 700;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: var(--spacing-md);
    padding-left: 2px;
  }
}

.metrics-row { margin-bottom: 0; }

.metric-card {
  background: var(--color-bg-secondary);
  border-top: 3px solid;
  border-radius: var(--radius-md);
  padding: var(--spacing-lg) var(--spacing-md);
  text-align: center;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s;

  &:hover { transform: translateY(-2px); }

  .metric-value {
    font-size: 24px;
    font-weight: 800;
  }

  .metric-label {
    color: var(--color-text-secondary);
    font-size: var(--font-size-xs);
    margin-top: var(--spacing-xs);
  }
}

.chart-box {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
}

.chart-title {
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}
</style>
