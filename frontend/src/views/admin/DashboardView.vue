<script setup>
import { ref, computed } from 'vue'

const timeRange = ref('today')

const metrics = [
  { label: 'DAU', value: '328', change: '+12%', color: '#4F46E5' },
  { label: 'MAU', value: '1,245', change: '+8%', color: '#059669' },
  { label: '次日留存', value: '45%', change: '+3%', color: '#D97706' },
  { label: '7日留存', value: '28%', change: '-2%', color: '#DC2626' },
]

// 用户增长趋势
const trendMonths = ['1月', '2月', '3月', '4月', '5月', '6月']
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 8, right: 8, top: 8, bottom: 24 },
  xAxis: { type: 'category', data: trendMonths },
  yAxis: { type: 'value' },
  series: [{
    name: '新增用户', type: 'line', smooth: true,
    data: [120, 185, 230, 280, 310, 340],
    areaStyle: { color: 'rgba(79,70,229,0.1)' },
    lineStyle: { color: '#4F46E5' },
  }],
}))

// CEFR 分布
const pieOption = computed(() => ({
  tooltip: {},
  legend: { bottom: 0 },
  series: [{
    type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
    data: [
      { value: 180, name: 'A1' }, { value: 320, name: 'A2' },
      { value: 420, name: 'B1' }, { value: 250, name: 'B2' },
      { value: 60, name: 'C1' }, { value: 15, name: 'C2' },
    ],
    label: { show: false },
  }],
}))
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">运营数据看板</h2>
      <el-radio-group v-model="timeRange" size="small">
        <el-radio-button value="today">今日</el-radio-button>
        <el-radio-button value="week">本周</el-radio-button>
        <el-radio-button value="month">本月</el-radio-button>
      </el-radio-group>
    </div>

    <el-row :gutter="16" class="metrics-row">
      <el-col :span="6" v-for="m in metrics" :key="m.label">
        <div class="metric-card" :style="{ borderTopColor: m.color }">
          <div class="metric-value" :style="{ color: m.color }">{{ m.value }}</div>
          <div class="metric-label">{{ m.label }}</div>
          <div class="metric-change" :style="{ color: m.change.startsWith('+') ? 'var(--color-success)' : 'var(--color-danger)' }">
            {{ m.change }}
          </div>
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
      <el-col :span="8">
        <div class="stat-box">
          <span class="stat-num">1,876</span><span class="stat-label">总学习时长(h)</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-box">
          <span class="stat-num">78%</span><span class="stat-label">对话完成率</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-box">
          <span class="stat-num">12.5</span><span class="stat-label">人均学习时长(h)</span>
        </div>
      </el-col>
    </el-row>
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
  .metric-change { font-size: var(--font-size-sm); font-weight: 500; }
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
