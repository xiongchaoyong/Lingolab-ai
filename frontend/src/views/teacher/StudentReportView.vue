<script setup>
import { ref } from 'vue'

const students = ref([
  { id: 1, name: 'Alice', level: 'B1', totalMinutes: 580, streak: 7, shadowScore: 78, conversationScore: 72, lastActive: '2小时前' },
  { id: 2, name: 'Bob', level: 'A2', totalMinutes: 320, streak: 3, shadowScore: 65, conversationScore: 60, lastActive: '昨天' },
  { id: 3, name: 'Charlie', level: 'B2', totalMinutes: 920, streak: 14, shadowScore: 85, conversationScore: 82, lastActive: '5分钟前' },
])

const showDetail = ref(false)
const selectedStudent = ref(null)
const detailsTab = ref('radar')

function viewStudent(student) {
  selectedStudent.value = student
  showDetail.value = true
}

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    indicator: [
      { name: '发音', max: 100 }, { name: '流利度', max: 100 },
      { name: '语法', max: 100 }, { name: '听力', max: 100 }, { name: '表达', max: 100 },
    ],
  },
  series: [{
    type: 'radar',
    data: [{ value: [78, 65, 72, 80, 60], name: '能力分布' }],
    lineStyle: { color: '#A78BFA' },
    areaStyle: { color: 'rgba(167,139,250,0.15)' },
  }],
}))
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">学生报告</h2>

    <el-table :data="students" stripe>
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="level" label="CEFR" width="70">
        <template #default="{ row }"><el-tag size="small">{{ row.level }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="totalMinutes" label="学习时长" width="100">
        <template #default="{ row }">{{ Math.floor(row.totalMinutes / 60) }}h</template>
      </el-table-column>
      <el-table-column prop="streak" label="连续(天)" width="80" />
      <el-table-column prop="shadowScore" label="发音分" width="80" />
      <el-table-column prop="conversationScore" label="对话分" width="80" />
      <el-table-column prop="lastActive" label="最近活跃" width="110" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewStudent(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDetail" :title="`${selectedStudent?.name} 学习详情`" width="600px">
      <template v-if="selectedStudent">
        <el-tabs v-model="detailsTab">
          <el-tab-pane label="能力雷达图" name="radar">
            <v-chart :option="radarOption" autoresize style="height:320px" />
          </el-tab-pane>
          <el-tab-pane label="学习记录" name="records">
            <el-timeline>
              <el-timeline-item timestamp="6月3日 14:30">完成发音练习 · 82分</el-timeline-item>
              <el-timeline-item timestamp="6月3日 10:15">完成AI对话 · 餐厅场景 · 75分</el-timeline-item>
              <el-timeline-item timestamp="6月2日 16:00">完成每日闯关 · 全通 · 130积分</el-timeline-item>
              <el-timeline-item timestamp="6月2日 09:30">完成听力训练 · 80分</el-timeline-item>
            </el-timeline>
          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button type="primary">点评学生</el-button>
      </template>
    </el-dialog>
  </div>
</template>
