<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const store = useAdminStore()
const loading = ref(false)
const dateRange = ref([])

onMounted(() => { loadDashboard() })

async function loadDashboard() {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    await store.fetchDashboard(params)
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  // 清空时直接加载（走默认30天）
  if (!dateRange.value || dateRange.value.length !== 2) {
    dateRange.value = []
  }
  loadDashboard()
}

// 快捷日期
function setDateRange(days) {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  dateRange.value = [
    start.toISOString().slice(0, 10),
    end.toISOString().slice(0, 10),
  ]
  loadDashboard()
}

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

// ===== 图表配置 =====

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

// 内容使用排行柱状图
const rankingOption = computed(() => {
  const ranking = store.dashboard?.content_ranking || []
  const names = ranking.map(r => r.name.length > 10 ? r.name.slice(0, 10) + '...' : r.name)
  const counts = ranking.map(r => r.count)
  const types = ranking.map(r => r.type)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (p) => {
        const items = Array.isArray(p) ? p : [p]
        const idx = items[0]?.dataIndex
        const name = ranking[idx]?.name || ''
        return `${name}<br/>${items.map(i => `${i.marker} ${i.seriesName}: ${i.value}`).join('<br/>')}`
      },
    },
    legend: { data: ['发音练习', '场景对话'], bottom: 0 },
    grid: { left: 8, right: 8, top: 8, bottom: 36 },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', name: '次数' },
    series: ['发音练习', '场景对话'].map(t => ({
      name: t, type: 'bar',
      data: ranking.map((r, i) => r.type === t ? r.count : null),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: t === '发音练习' ? '#A78BFA' : '#34D399',
      },
      barGap: '20%',
    })),
  }
})

// 转化漏斗图
const funnelOption = computed(() => {
  const funnel = store.dashboard?.conversion_funnel || {}
  const stages = [
    { name: '注册', value: funnel.registered || 0 },
    { name: '完成测评', value: funnel.assessed || 0 },
    { name: '首次练习', value: funnel.first_practice || 0 },
    { name: '7日留存', value: funnel.retained_7d || 0 },
  ]
  const maxVal = Math.max(...stages.map(s => s.value), 1)
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const rate = stages[0].value > 0 ? (p.value / stages[0].value * 100).toFixed(1) : 0
        return `${p.name}: ${p.value}<br/>相对注册: ${rate}%`
      },
    },
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: 'value', show: false, max: maxVal },
    yAxis: { type: 'category', data: stages.map(s => s.name), axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: stages.map((s, i) => ({
        value: s.value,
        itemStyle: {
          color: ['#A78BFA', '#60A5FA', '#34D399', '#FBBF24'][i],
          borderRadius: [0, 8, 8, 0],
        },
      })),
      barWidth: 32,
      label: { show: true, position: 'right', formatter: '{c}' },
    }],
  }
})

// ===== 导出 Excel (CSV) =====
function exportCSV() {
  const report = store.dashboard?.daily_report || []
  if (!report.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['日期', 'DAU', '新增用户', '发音练习', '对话', '任务完成']
  const rows = report.map(r => [
    r.date, r.dau, r.new_users, r.practice_count, r.conversation_count, r.tasks_completed,
  ])
  const BOM = '\uFEFF'
  const csv = BOM + [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `运营日报_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>

<template>
  <div class="content-card dashboard-page">
    <!-- 头部：标题 + 日期筛选 + 快捷按钮 + 导出 -->
    <div class="dash-header">
      <h2 class="page-title" style="margin-bottom:0;">运营数据看板</h2>
      <div class="dash-controls">
        <el-button-group class="date-presets">
          <el-button size="small" @click="setDateRange(7)">近7天</el-button>
          <el-button size="small" @click="setDateRange(30)">近30天</el-button>
          <el-button size="small" @click="setDateRange(90)">近90天</el-button>
        </el-button-group>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始"
          end-placeholder="结束"
          size="small"
          style="width: 240px;"
          @change="handleDateChange"
        />
        <el-button size="small" :icon="Download" type="primary" @click="exportCSV">导出日报</el-button>
      </div>
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

      <!-- 图表行1：内容排行 + 转化漏斗 -->
      <el-row :gutter="16" style="margin-top: var(--spacing-lg);">
        <el-col :span="14">
          <div class="chart-box">
            <h4 class="chart-title">内容使用排行（所选时段）</h4>
            <v-chart v-if="(store.dashboard.content_ranking || []).length" :option="rankingOption" autoresize style="height: 300px" />
            <el-empty v-else description="暂无排行数据" :image-size="60" />
          </div>
        </el-col>
        <el-col :span="10">
          <div class="chart-box">
            <h4 class="chart-title">转化漏斗（所选时段）</h4>
            <v-chart v-if="(store.dashboard.conversion_funnel || {}).registered" :option="funnelOption" autoresize style="height: 300px" />
            <el-empty v-else description="暂无漏斗数据" :image-size="60" />
          </div>
        </el-col>
      </el-row>

      <!-- 图表行2：7日DAU + CEFR分布 -->
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

      <!-- 图表行3：用户增长 + 练习类型 -->
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
.dashboard-page {
  padding-bottom: var(--spacing-xl);
}

.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.dash-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.date-presets {
  margin-right: var(--spacing-xs);
}

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

@media (max-width: 768px) {
  .dash-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .dash-controls {
    flex-wrap: wrap;
  }
}
</style>
