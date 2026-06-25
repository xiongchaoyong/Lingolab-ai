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

const metrics = computed(() => {
  const d = store.dashboard?.metrics
  if (!d) return []
  return [
    { label: 'DAU', value: String(d.dau), color: '#A78BFA' },
    { label: 'MAU', value: String(d.mau), color: '#C4B5FD' },
    { label: '总用户', value: String(d.total_users), color: '#FDBA74' },
    { label: '活跃用户', value: String(d.active_users), color: '#FDA4AF' },
  ]
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

const typeDist = computed(() => {
  const dist = store.dashboard?.content_type_distribution || {}
  return Object.entries(dist).map(([name, value]) => ({ name, value }))
})
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">运营数据看板</h2>
    </div>

    <div v-if="loading" style="text-align:center;padding:60px 0;">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <template v-else-if="store.dashboard">
      <el-row :gutter="16" class="metrics-row">
        <el-col :span="6" v-for="m in metrics" :key="m.label">
          <div class="metric-card" :style="{ borderTopColor: m.color }">
            <div class="metric-value" :style="{ color: m.color }">{{ m.value }}</div>
            <div class="metric-label">{{ m.label }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: var(--spacing-lg);">
        <el-col :span="14">
          <div class="chart-box">
            <h4 class="chart-title">用户增长趋势</h4>
            <v-chart :option="lineOption" autoresize style="height: 300px" />
          </div>
        </el-col>
        <el-col :span="10">
          <div class="chart-box">
            <h4 class="chart-title">CEFR 等级分布</h4>
            <v-chart :option="pieOption" autoresize style="height: 300px" />
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: var(--spacing-lg);">
        <el-col :span="8" v-for="t in typeDist" :key="t.name">
          <div class="stat-box">
            <span class="stat-num">{{ t.value }}</span>
            <span class="stat-label">{{ t.name }} 练习次数</span>
          </div>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="暂无数据" />
  </div>
</template>

<style lang="scss" scoped>
.metrics-row { margin-bottom: 0; }
.metric-card {
  background: var(--color-bg-secondary); border-top: 3px solid;
  border-radius: var(--radius-md); padding: var(--spacing-xl); text-align: center;
  box-shadow: var(--shadow-card);
  .metric-value { font-size: 28px; font-weight: 800; }
  .metric-label { color: var(--color-text-secondary); font-size: var(--font-size-sm); margin: var(--spacing-xs) 0; }
}
.chart-box {
  background: var(--color-bg-secondary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--spacing-lg);
}
.chart-title { font-weight: 600; margin-bottom: var(--spacing-md); }
.stat-box {
  background: rgba(var(--color-primary-rgb), 0.05); border-radius: var(--radius-md);
  padding: var(--spacing-lg) var(--spacing-xl); text-align: center;
  .stat-num { font-size: var(--font-size-xl); font-weight: 700; color: var(--color-primary); margin-right: var(--spacing-sm); }
  .stat-label { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
}
</style>