<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTeacherDashboardApi } from '@/api/admin'
import {
  School, DataLine, Timer, EditPen, User, TrendCharts,
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(true)
const data = ref(null)

onMounted(async () => {
  try {
    data.value = await getTeacherDashboardApi()
  } finally {
    loading.value = false
  }
})

function goTo(path) {
  router.push(path)
}

const contentTypeLabel = { pronunciation: '跟读练习', conversation: '场景对话', dubbing: '配音挑战' }

function formatDate(iso) {
  if (!iso) return ''
  return iso.slice(0, 10)
}
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <div>
        <h2 class="page-title">教师工作台</h2>
        <p class="page-sub">概览班级和学生整体情况</p>
      </div>
    </div>

    <div v-if="loading" class="dashboard-loading" v-loading="true">
      <p>加载中...</p>
    </div>

    <template v-else-if="data">
      <!-- 核心指标卡片 -->
      <div class="metric-cards">
        <div class="metric-card" @click="goTo('/teacher/classes')">
          <el-icon :size="24" color="#7C6FF7"><School /></el-icon>
          <div class="mc-body">
            <span class="mc-num">{{ data.total_classes }}</span>
            <span class="mc-label">班级</span>
          </div>
          <span class="mc-detail">平均 {{ data.avg_class_size }} 人/班</span>
        </div>

        <div class="metric-card">
          <el-icon :size="24" color="#34D399"><User /></el-icon>
          <div class="mc-body">
            <span class="mc-num">{{ data.total_students }}</span>
            <span class="mc-label">学生</span>
          </div>
          <span class="mc-detail">今日 {{ data.active_students_today }} 人活跃</span>
        </div>

        <div class="metric-card" @click="goTo('/teacher/homework')">
          <el-icon :size="24" color="#F59E0B"><EditPen /></el-icon>
          <div class="mc-body">
            <span class="mc-num">{{ data.pending_reviews }}</span>
            <span class="mc-label">待点评</span>
          </div>
          <span class="mc-detail">共 {{ data.total_assignments }} 次作业</span>
        </div>

        <div class="metric-card">
          <el-icon :size="24" color="#3B82F6"><TrendCharts /></el-icon>
          <div class="mc-body">
            <span class="mc-num">{{ data.active_students_today }}</span>
            <span class="mc-label">今日活跃</span>
          </div>
          <span class="mc-detail">学生参与学习</span>
        </div>
      </div>

      <!-- 班级学生分布 -->
      <div v-if="data.class_student_counts?.length" class="dashboard-row">
        <div class="dashboard-card card--half">
          <h3 class="card-title">班级学生分布</h3>
          <div class="class-bar-list">
            <div v-for="c in data.class_student_counts" :key="c.name" class="class-bar-item">
              <span class="cbi-name">{{ c.name }}</span>
              <div class="cbi-bar-wrap">
                <div
                  class="cbi-bar"
                  :style="{ width: Math.max(c.count / Math.max(...data.class_student_counts.map(x => x.count)) * 100, 8) + '%' }"
                ></div>
              </div>
              <span class="cbi-num">{{ c.count }}人</span>
            </div>
          </div>
        </div>

        <!-- 最近布置的作业 -->
        <div class="dashboard-card card--half">
          <h3 class="card-title">
            最近布置的作业
            <el-button size="small" text type="primary" @click="goTo('/teacher/homework')">全部作业</el-button>
          </h3>
          <div v-if="data.recent_assignments?.length" class="recent-assignments">
            <div v-for="a in data.recent_assignments" :key="a.id" class="ra-item">
              <div class="ra-title">{{ a.title }}</div>
              <div class="ra-meta">
                <el-tag size="small">{{ contentTypeLabel[a.content_type] || a.content_type }}</el-tag>
                <span>{{ a.class_name }}</span>
                <span class="ra-date">{{ formatDate(a.created_at) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-text">暂无作业</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.page-header {
  margin-bottom: var(--spacing-xl);
  .page-sub { color: var(--color-text-secondary); font-size: var(--font-size-sm); margin-top: 2px; }
}

.dashboard-loading {
  display: flex; justify-content: center;
  padding: var(--spacing-xxxl) 0; color: var(--color-text-secondary);
}

.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.metric-card {
  display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm);
  padding: var(--spacing-xl); background: var(--color-bg-secondary);
  border: 1px solid var(--color-border); border-radius: var(--radius-lg);
  cursor: default; transition: box-shadow 0.2s;
  &:hover { box-shadow: 0 2px 16px rgba(0,0,0,.06); }
  .mc-num { font-size: 32px; font-weight: 700; color: var(--color-text-primary); }
  .mc-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
  .mc-body { display: flex; flex-direction: column; align-items: center; }
  .mc-detail { font-size: var(--font-size-xs); color: var(--color-text-disabled); }
}

.dashboard-row {
  display: flex; gap: var(--spacing-xl);
}

.dashboard-card {
  background: var(--color-bg-secondary); border: 1px solid var(--color-border);
  border-radius: var(--radius-lg); padding: var(--spacing-xl);
  &.card--half { flex: 1; }
}

.card-title {
  font-size: var(--font-size-base); font-weight: 600; margin: 0 0 var(--spacing-lg);
  display: flex; align-items: center; justify-content: space-between;
}

.class-bar-list {
  display: flex; flex-direction: column; gap: var(--spacing-md);
}

.class-bar-item {
  display: flex; align-items: center; gap: var(--spacing-md);
  .cbi-name { width: 80px; font-size: var(--font-size-sm); font-weight: 500; flex-shrink: 0; }
  .cbi-bar-wrap { flex: 1; height: 24px; background: var(--color-border); border-radius: 4px; overflow: hidden; }
  .cbi-bar { height: 100%; background: linear-gradient(90deg, #7C6FF7, #A78BFA); border-radius: 4px; transition: width 0.3s; min-width: 8px; }
  .cbi-num { font-size: var(--font-size-sm); color: var(--color-text-secondary); width: 36px; text-align: right; }
}

.recent-assignments {
  display: flex; flex-direction: column; gap: var(--spacing-md);
}

.ra-item {
  padding: var(--spacing-md); background: var(--color-bg-primary);
  border-radius: var(--radius-md);
  .ra-title { font-weight: 600; font-size: var(--font-size-sm); margin-bottom: 6px; }
  .ra-meta { display: flex; align-items: center; gap: var(--spacing-sm); font-size: var(--font-size-xs); color: var(--color-text-secondary); }
  .ra-date { margin-left: auto; color: var(--color-text-disabled); }
}

.empty-text {
  text-align: center; color: var(--color-text-disabled); padding: var(--spacing-xl);
  font-size: var(--font-size-sm);
}
</style>
