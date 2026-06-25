import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getRadarDataApi,
  getTrendDataApi,
  getHeatmapDataApi,
  getStatsApi,
} from '@/api/progress'

export const useProgressStore = defineStore('progress', () => {
  // ===== 状态 =====
  const timeRange = ref('week')
  const loading = ref(false)

  const radarData = ref({ dimensions: [], range: 'week' })
  const trendData = ref({ points: [], range: 'week' })
  const heatmapData = ref({ days: [], year: new Date().getFullYear() })
  const stats = ref([])

  const isEmpty = computed(() => {
    return stats.value.length > 0 && stats.value.every(s => s.value === '0')
  })

  // ===== ECharts 配置 =====

  const radarOption = computed(() => {
    const dims = radarData.value.dimensions || []
    const indicator = dims.map(d => ({ name: d.name, max: 100 }))
    const current = dims.map(d => d.current)
    const previous = dims.map(d => d.previous)

    return {
      tooltip: {},
      legend: { data: ['当前', '上次'], bottom: 0 },
      radar: {
        indicator,
        center: ['50%', '55%'],
      },
      series: [{
        type: 'radar',
        data: [
          { value: current, name: '当前', lineStyle: { color: '#A78BFA' }, areaStyle: { color: 'rgba(167,139,250,0.15)' } },
          { value: previous, name: '上次', lineStyle: { color: '#C4B5D4', type: 'dashed' }, areaStyle: { color: 'rgba(196,181,212,0.12)' } },
        ],
      }],
    }
  })

  const lineOption = computed(() => {
    const points = trendData.value.points || []
    const labels = points.map(p => p.date)
    const pronunciation = points.map(p => p.pronunciation)
    const fluency = points.map(p => p.fluency)

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['发音准确率', '流利度'], bottom: 0 },
      grid: { left: 8, right: 8, top: 8, bottom: 24 },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value', min: 0, max: 100 },
      series: [
        { name: '发音准确率', type: 'line', data: pronunciation, smooth: true, lineStyle: { color: '#A78BFA' }, itemStyle: { color: '#A78BFA' } },
        { name: '流利度', type: 'line', data: fluency, smooth: true, lineStyle: { color: '#C4B5FD' }, itemStyle: { color: '#C4B5FD' } },
      ],
    }
  })

  const calendarOption = computed(() => {
    const days = heatmapData.value.days || []
    const data = days.map(d => [d.date, d.level])

    return {
      tooltip: {
        formatter: (p) => `${p.data[0]}: ${days.find(d => d.date === p.data[0])?.count || 0} 次活动`,
      },
      visualMap: {
        min: 0, max: 3,
        orient: 'horizontal', left: 'center', bottom: 0,
        inRange: { color: ['#E2E8F0', '#A7F3D0', '#6EE7B7', '#059669'] },
        textStyle: { color: '#64748B' },
      },
      calendar: {
        range: String(heatmapData.value.year || new Date().getFullYear()),
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

  const statCards = computed(() => {
    if (!stats.value || stats.value.length === 0) return []
    return stats.value.map(s => ({
      label: s.label,
      value: s.value,
      unit: s.unit,
    }))
  })

  // ===== 方法 =====

  async function fetchAll(range = 'week') {
    loading.value = true
    try {
      const [radar, trend, heatmap, statsResult] = await Promise.all([
        getRadarDataApi(range),
        getTrendDataApi(range),
        getHeatmapDataApi(new Date().getFullYear()),
        getStatsApi(),
      ])
      radarData.value = radar
      trendData.value = trend
      heatmapData.value = heatmap
      stats.value = statsResult.stats || []
    } catch {
      // 错误由拦截器统一处理
    } finally {
      loading.value = false
    }
  }

  function setTimeRange(range) {
    timeRange.value = range
    fetchAll(range)
  }

  return {
    timeRange, loading, isEmpty,
    radarData, trendData, heatmapData, stats,
    radarOption, lineOption, calendarOption, statCards,
    fetchAll, setTimeRange,
  }
})