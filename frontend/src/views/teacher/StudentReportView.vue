<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, CalendarComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  getAllStudentsApi, getStudentDetailApi,
  getStudentTrendApi, getStudentCheckinStatsApi,
} from '@/api/admin'

use([CanvasRenderer, RadarChart, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, CalendarComponent])

const students = ref([])
const loading = ref(false)
const showDetail = ref(false)
const selectedStudent = ref(null)
const detailLoading = ref(false)
const studentDetail = ref(null)
const detailsTab = ref('radar')

// 趋势和打卡数据
const trendData = ref(null)
const checkinData = ref(null)

onMounted(() => { loadStudents() })

async function loadStudents() {
  loading.value = true
  try {
    const res = await getAllStudentsApi()
    students.value = res.students || []
  } catch {
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

async function viewStudent(student) {
  selectedStudent.value = student
  showDetail.value = true
  detailLoading.value = true
  studentDetail.value = null
  trendData.value = null
  checkinData.value = null
  try {
    const [detail, trend, checkin] = await Promise.all([
      getStudentDetailApi(student.id),
      getStudentTrendApi(student.id).catch(() => null),
      getStudentCheckinStatsApi(student.id).catch(() => null),
    ])
    studentDetail.value = detail
    trendData.value = trend
    checkinData.value = checkin
  } catch {
    ElMessage.error('加载学生详情失败')
  } finally {
    detailLoading.value = false
  }
}

const radarOption = computed(() => {
  const dims = studentDetail.value?.dimension_averages || {}
  const labels = Object.keys(dims)
  const values = Object.values(dims)
  return {
    tooltip: {},
    radar: { indicator: labels.map(l => ({ name: l, max: 100 })) },
    series: [{
      type: 'radar',
      data: [{ value: values, name: '能力分布' }],
      lineStyle: { color: '#A78BFA' },
      areaStyle: { color: 'rgba(167,139,250,0.15)' },
    }],
  }
})

const trendOption = computed(() => {
  const trend = trendData.value?.trend || []
  const dates = trend.map(t => t.date?.slice(5)) // "MM-DD"
  const dimKeys = ['pronunciation', 'fluency', 'grammar', 'vocabulary']
  const dimLabels = ['发音', '流利度', '语法', '词汇运用']
  const colors = ['#A78BFA', '#34D399', '#F59E0B', '#3B82F6']
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: dimLabels, bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 40, right: 16, top: 16, bottom: 36 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: dimKeys.map((k, i) => ({
      name: dimLabels[i], type: 'line', data: trend.map(t => t[k] || 0),
      smooth: true, lineStyle: { color: colors[i] },
      itemStyle: { color: colors[i] },
    })),
  }
})

const checkinOption = computed(() => {
  const checkins = checkinData.value?.checkins || []
  const dates = checkins.map(c => c.date?.slice(5))
  const counts = checkins.map(c => c.completed)
  return {
    tooltip: {},
    grid: { left: 40, right: 16, top: 16, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45, fontSize: 9, interval: 2 } },
    yAxis: { type: 'value', name: '次数' },
    series: [{
      type: 'bar', data: counts,
      itemStyle: {
        color: '#7C6FF7',
        borderRadius: [3, 3, 0, 0],
      },
    }],
  }
})
</script>

<template>
  <div class="content-card report-page">
    <h2 class="page-title">学生报告</h2>

    <div class="report-table-wrap">
      <el-table v-loading="loading" :data="students" stripe empty-text="暂无学生数据" height="100%">
      <el-table-column prop="username" label="姓名" width="120" />
      <el-table-column prop="level_final" label="CEFR" width="80">
        <template #default="{ row }"><el-tag size="small">{{ row.level_final }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="total_minutes" label="学习时长" width="100">
        <template #default="{ row }">{{ Math.floor(row.total_minutes / 60) }}h</template>
      </el-table-column>
      <el-table-column prop="last_active" label="最近活跃" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewStudent(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog v-model="showDetail" :title="`${selectedStudent?.username} 学习详情`" width="680px"
      destroy-on-close :close-on-click-modal="false">
      <div v-if="detailLoading" v-loading="true" style="height: 200px;"></div>
      <template v-else-if="studentDetail">
        <div class="detail-top-bar">
          <div><strong>CEFR 等级：</strong><el-tag size="small">{{ studentDetail.level_final }}</el-tag></div>
          <div><strong>学习目标：</strong>{{ studentDetail.learning_goal || '-' }}</div>
          <div><strong>记录数：</strong>{{ studentDetail.total_records }}</div>
          <div v-if="checkinData">
            <strong>连续打卡：</strong>
            <el-tag size="small" type="warning">{{ checkinData.streak }} 天</el-tag>
            <span class="checkin-rate">（打卡率 {{ checkinData.completion_rate }}%）</span>
          </div>
        </div>
        <el-tabs v-model="detailsTab">
          <el-tab-pane label="能力雷达图" name="radar">
            <v-chart
              v-if="Object.keys(studentDetail.dimension_averages || {}).length > 0"
              :option="radarOption" autoresize style="height: 320px;"
            />
            <p v-else class="empty-chart">暂无维度分数数据</p>
          </el-tab-pane>
          <el-tab-pane label="分数趋势" name="trend">
            <v-chart
              v-if="trendData?.trend?.length > 0"
              :option="trendOption" autoresize style="height: 320px;"
            />
            <p v-else class="empty-chart">暂无趋势数据</p>
          </el-tab-pane>
          <el-tab-pane label="打卡统计" name="checkin">
            <v-chart
              v-if="checkinData?.checkins?.length > 0"
              :option="checkinOption" autoresize style="height: 280px;"
            />
            <p v-else class="empty-chart">暂无打卡数据</p>
          </el-tab-pane>
          <el-tab-pane label="最近活动" name="records">
            <el-timeline v-if="studentDetail.recent_activities?.length">
              <el-timeline-item
                v-for="(act, i) in studentDetail.recent_activities"
                :key="i"
                :timestamp="act.created_at ? new Date(act.created_at).toLocaleString('zh-CN') : ''"
              >
                {{ act.dimension }} · {{ act.score }}分
              </el-timeline-item>
            </el-timeline>
            <p v-else class="empty-chart">暂无活动记录</p>
          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.report-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - var(--spacing-xl) * 2);
}

.report-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.detail-top-bar {
  display: flex; gap: var(--spacing-lg); margin-bottom: var(--spacing-md);
  flex-wrap: wrap; font-size: var(--font-size-sm);
  .checkin-rate { color: var(--color-text-secondary); font-size: var(--font-size-xs); }
}

.empty-chart {
  color: var(--color-text-disabled); text-align: center; padding: 40px 0;
  font-size: var(--font-size-sm);
}
</style>
