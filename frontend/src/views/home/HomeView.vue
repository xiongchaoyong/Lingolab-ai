<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, ChatDotRound, Reading, WarningFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useProgressStore } from '@/stores/progress'
import { usePredictionStore } from '@/stores/prediction'
import { getMyAssignmentsApi, submitAssignmentApi } from '@/api/student'

const authStore = useAuthStore()
const progressStore = useProgressStore()
const predStore = usePredictionStore()

const loading = ref(true)

// ========== 进度追踪状态 ==========
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

// ========== 作业状态 ==========
const assignments = ref([])
const hwLoading = ref(false)
const showSubmitDialog = ref(false)
const currentAssignment = ref(null)
const audioUrl = ref('')
const submitting = ref(false)

const levelLabel = computed(() => {
  const level = authStore.userInfo?.level_final
  if (!level) return null
  const map = { A1: '入门', A2: '基础', B1: '进阶', B2: '中高级', C1: '流利', C2: '精通' }
  return `${level} · ${map[level] || ''}`
})

onMounted(async () => {
  await Promise.all([
    progressStore.fetchAll(),
    predStore.fetchPrediction(),
    predStore.checkAlerts(),
    loadAssignments(),
  ])
  loading.value = false
})

// ========== 作业方法 ==========
async function loadAssignments() {
  hwLoading.value = true
  try {
    const res = await getMyAssignmentsApi()
    assignments.value = res.assignments || []
  } catch {
    // 静默失败，作业不是必需的
  } finally {
    hwLoading.value = false
  }
}

function openSubmit(assignment) {
  currentAssignment.value = assignment
  audioUrl.value = ''
  showSubmitDialog.value = true
}

async function handleSubmit() {
  if (!audioUrl.value) return
  submitting.value = true
  try {
    await submitAssignmentApi(currentAssignment.value.id, audioUrl.value)
    ElMessage.success('提交成功')
    showSubmitDialog.value = false
    await loadAssignments()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

function getContentTypeLabel(type) {
  const map = { pronunciation: '跟读练习', conversation: '场景对话', dubbing: '配音挑战' }
  return map[type] || type
}

function getStatusTag(submission) {
  if (!submission) return 'info'
  if (submission.status === 'reviewed') return 'success'
  return 'warning'
}

function getStatusLabel(submission) {
  if (!submission) return '未提交'
  if (submission.status === 'reviewed') return '已点评'
  return '已提交'
}
</script>

<template>
  <div class="home-page">
    <!-- ========== 欢迎区 ========== -->
    <div class="welcome-section">
      <el-avatar :size="48" :src="authStore.userInfo?.avatar" icon="UserFilled" class="welcome-avatar" />
      <div>
        <h2 class="page-title">
          欢迎回来，{{ authStore.userInfo?.username || '同学' }}
        </h2>
        <p class="welcome-subtitle">
          <template v-if="levelLabel">当前等级：{{ levelLabel }}</template>
          <template v-else>今日学习进度</template>
        </p>
      </div>
    </div>

    <!-- ========== 统计卡片 ========== -->
    <el-row v-loading="loading" :gutter="16" class="stats-row">
      <el-col v-for="stat in progressStore.statCards" :key="stat.label" :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stat.value }}<small>{{ stat.unit }}</small></div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ========== 快捷入口 ========== -->
    <h3 class="section-title">开始练习</h3>
    <el-row :gutter="16" class="quick-actions">
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/pronunciation')">
          <el-icon :size="36" color="#A78BFA"><Microphone /></el-icon>
          <h4>发音评测</h4>
          <p>跟读标准发音，获取多维度评分</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/voice-chat')">
          <el-icon :size="36" color="#C4B5FD"><ChatDotRound /></el-icon>
          <h4>AI 语音对话</h4>
          <p>自由对话 + 角色扮演，沉浸式口语练习</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="action-card" @click="$router.push('/grammar')">
          <el-icon :size="36" color="#FDBA74"><Reading /></el-icon>
          <h4>语法纠错</h4>
          <p>AI 智能语法检查与润色建议</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- ========== 进度追踪 ========== -->
    <div class="section-divider">
      <h3 class="section-title">进度追踪</h3>
      <el-radio-group v-model="progressStore.timeRange" size="small" @change="progressStore.setTimeRange">
        <el-radio-button value="day">天</el-radio-button>
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
        <el-radio-button value="all">全部</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 空状态 -->
    <div v-if="progressStore.isEmpty && !progressStore.loading" class="empty-state">
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
            <v-chart v-if="progressStore.radarData.dimensions?.length" :option="progressStore.radarOption" autoresize style="height: 320px" />
            <el-empty v-else description="暂无雷达图数据" :image-size="60" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-box">
            <h4 class="chart-title">趋势折线图</h4>
            <v-chart v-if="progressStore.trendData.points?.length" :option="progressStore.lineOption" autoresize style="height: 320px" />
            <el-empty v-else description="暂无趋势数据" :image-size="60" />
          </div>
        </el-col>
      </el-row>

      <!-- 日历热力图 -->
      <div class="chart-box" style="margin-top: var(--spacing-lg);">
        <h4 class="chart-title">学习日历</h4>
        <v-chart v-if="progressStore.heatmapData.days?.length" :option="progressStore.calendarOption" autoresize style="height: 200px" />
        <el-empty v-else description="暂无日历数据" :image-size="60" />
      </div>

      <!-- 学习预测 -->
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

      <!-- 预警通知 -->
      <div class="chart-box" style="margin-top: var(--spacing-base);" v-if="predStore.alerts.length">
        <h4 class="chart-title">系统提醒</h4>
        <div v-for="alert in predStore.alerts" :key="alert.type" class="alert-item">
          <el-icon color="var(--color-warning)"><WarningFilled /></el-icon>
          <span>{{ alert.message }}</span>
        </div>
      </div>
    </template>

    <!-- ========== 我的作业 ========== -->
    <h3 class="section-title" style="margin-top: var(--spacing-xxl);">我的作业</h3>
    <div v-loading="hwLoading" class="homework-section">
      <template v-if="!hwLoading && assignments.length === 0">
        <el-empty description="暂无作业" :image-size="60" />
      </template>
      <el-table v-else :data="assignments" stripe>
        <el-table-column prop="title" label="作业标题" min-width="160" />
        <el-table-column prop="class_name" label="班级" width="140" />
        <el-table-column prop="content_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getContentTypeLabel(row.content_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="120">
          <template #default="{ row }">{{ row.due_date?.slice(0, 10) || '-' }}</template>
        </el-table-column>
        <el-table-column label="提交状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusTag(row.my_submission)">
              {{ getStatusLabel(row.my_submission) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AI评分" width="80">
          <template #default="{ row }">
            {{ row.my_submission?.score != null ? Math.round(row.my_submission.score) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="教师点评" min-width="160">
          <template #default="{ row }">
            <template v-if="row.my_submission?.teacher_feedback">
              <span style="color: var(--color-primary);">{{ row.my_submission.teacher_feedback }}</span>
              <span v-if="row.my_submission.teacher_score != null" style="margin-left: 8px; color: var(--color-text-secondary);">
                {{ Math.round(row.my_submission.teacher_score) }}分
              </span>
            </template>
            <span v-else style="color: var(--color-text-disabled);">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              :type="row.my_submission ? 'default' : 'primary'"
              @click="openSubmit(row)"
            >
              {{ row.my_submission ? '重新提交' : '提交' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 提交作业对话框 -->
    <el-dialog v-model="showSubmitDialog" title="提交作业" width="460px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="作业标题">
          <el-input :model-value="currentAssignment?.title" disabled />
        </el-form-item>
        <el-form-item label="录音文件 URL">
          <el-input v-model="audioUrl" placeholder="输入录音文件的 URL 地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :disabled="!audioUrl" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.home-page {
  .welcome-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);

    .welcome-avatar {
      flex-shrink: 0;
    }

    .page-title {
      font-family: var(--font-heading);
      font-size: var(--font-size-xl);
      font-weight: 700;
      margin: 0;
    }

    .welcome-subtitle {
      margin-top: 4px;
      color: var(--color-text-secondary);
      font-family: var(--font-body);
    }
  }

  .stats-row {
    margin-bottom: var(--spacing-xxl);
  }

  .stat-card {
    text-align: center;
    transition: all var(--transition-base);
    margin-bottom: var(--spacing-base);

    &:hover {
      transform: translateY(-2px);
    }

    .stat-value {
      font-family: var(--font-heading);
      font-size: 24px;
      font-weight: 700;
      color: var(--color-primary);
      small {
        font-size: 14px;
        font-weight: 400;
        color: var(--color-text-secondary);
        margin-left: 2px;
      }
    }

    .stat-label {
      margin-top: var(--spacing-xs);
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
      font-family: var(--font-body);
    }
  }

  .section-title {
    font-family: var(--font-heading);
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin-bottom: var(--spacing-base);
  }

  .quick-actions {
    margin-bottom: var(--spacing-xxl);

    .action-card {
      cursor: pointer;
      text-align: center;
      padding: var(--spacing-xl) var(--spacing-base);
      transition: all var(--transition-base);

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
      }

      h4 {
        font-family: var(--font-heading);
        margin: var(--spacing-md) 0 var(--spacing-sm);
        font-size: var(--font-size-base);
      }

      p {
        color: var(--color-text-secondary);
        font-family: var(--font-body);
        font-size: var(--font-size-sm);
      }
    }
  }

  .section-divider {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--spacing-lg);

    .section-title {
      margin-bottom: 0;
    }
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

  .homework-section {
    min-height: 60px;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .home-page .stats-row .stat-value {
    font-size: 18px;
  }
}
</style>
