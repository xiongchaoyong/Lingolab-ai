<script setup>
import { ref, onMounted, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const store = useAdminStore()
const loading = ref(false)

const showAssignDialog = ref(false)
const showSubmissionsDialog = ref(false)
const showReviewDialog = ref(false)
const currentSubmission = ref(null)
const reviewForm = ref({ teacher_feedback: '', teacher_score: null })

const newHomework = ref({
  class_id: null,
  title: '',
  description: '',
  content_type: 'pronunciation',
  content_ids: [],
  due_date: null,
})

const contentTypes = [
  { value: 'pronunciation', label: '跟读练习' },
  { value: 'conversation', label: '场景对话' },
  { value: 'dubbing', label: '配音挑战' },
]

onMounted(() => {
  store.fetchAssignments()
  store.fetchClasses()
})

const classOptions = computed(() =>
  store.classes.map(c => ({ value: c.id, label: c.name }))
)

function getContentTypeLabel(type) {
  const item = contentTypes.find(t => t.value === type)
  return item ? item.label : type
}

async function assignHomework() {
  if (!newHomework.value.title || !newHomework.value.class_id) return
  loading.value = true
  try {
    const data = {
      ...newHomework.value,
      due_date: newHomework.value.due_date
        ? new Date(newHomework.value.due_date).toISOString()
        : null,
    }
    await store.createAssignment(data)
    ElMessage.success('作业布置成功')
    showAssignDialog.value = false
    newHomework.value = { class_id: null, title: '', description: '', content_type: 'pronunciation', content_ids: [], due_date: null }
  } catch (e) {
    ElMessage.error('布置失败')
  } finally {
    loading.value = false
  }
}

async function viewSubmissions(assignment) {
  try {
    await store.fetchSubmissions(assignment.id)
    showSubmissionsDialog.value = true
  } catch (e) {
    ElMessage.error('获取提交列表失败')
  }
}

function openReview(sub) {
  currentSubmission.value = sub
  reviewForm.value = {
    teacher_feedback: sub.teacher_feedback || '',
    teacher_score: sub.teacher_score,
  }
  showReviewDialog.value = true
}

async function submitReview() {
  loading.value = true
  try {
    await store.reviewSubmission(currentSubmission.value.id, reviewForm.value)
    ElMessage.success('点评成功')
    showReviewDialog.value = false
    // 刷新提交列表
    const assignmentId = currentSubmission.value.assignment_id
    await store.fetchSubmissions(assignmentId)
  } catch (e) {
    ElMessage.error('点评失败')
  } finally {
    loading.value = false
  }
}

function getStatusTag(status) {
  return status === 'reviewed' ? 'success' : 'warning'
}

function getStatusLabel(status) {
  return status === 'reviewed' ? '已点评' : '待点评'
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">作业管理</h2>
      <el-button type="primary" :icon="Plus" @click="showAssignDialog = true">布置作业</el-button>
    </div>

    <el-table :data="store.assignments" stripe v-loading="loading">
      <el-table-column prop="title" label="作业标题" min-width="160" />
      <el-table-column prop="class_name" label="班级" width="140" />
      <el-table-column prop="content_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.content_type === 'pronunciation' ? 'primary' : row.content_type === 'conversation' ? 'success' : 'warning'">
            {{ getContentTypeLabel(row.content_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="布置时间" width="120">
        <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
      </el-table-column>
      <el-table-column prop="due_date" label="截止" width="120">
        <template #default="{ row }">{{ row.due_date?.slice(0, 10) || '-' }}</template>
      </el-table-column>
      <el-table-column label="完成率" width="120">
        <template #default="{ row }">
          <el-progress :percentage="Math.round(row.completion_rate)" :stroke-width="6" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewSubmissions(row)">查看提交</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="store.assignments.length === 0 && !loading" description="暂无作业" />

    <!-- 布置作业对话框 -->
    <el-dialog v-model="showAssignDialog" title="布置作业" width="480px">
      <el-form label-position="top">
        <el-form-item label="作业标题">
          <el-input v-model="newHomework.title" placeholder="如：Unit 3 跟读练习" maxlength="200" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="newHomework.class_id" style="width:100%" placeholder="选择班级">
            <el-option v-for="c in classOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="作业类型">
          <el-radio-group v-model="newHomework.content_type">
            <el-radio v-for="t in contentTypes" :key="t.value" :value="t.value">{{ t.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="newHomework.due_date" type="date" style="width:100%" placeholder="选填" />
        </el-form-item>
        <el-form-item label="作业说明">
          <el-input v-model="newHomework.description" type="textarea" :rows="3" placeholder="具体要求和说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="assignHomework" :disabled="!newHomework.title || !newHomework.class_id" :loading="loading">布置</el-button>
      </template>
    </el-dialog>

    <!-- 提交列表对话框 -->
    <el-dialog v-model="showSubmissionsDialog" title="作业提交" width="700px">
      <el-table :data="store.submissions" stripe max-height="400">
        <el-table-column prop="username" label="学生" width="120" />
        <el-table-column prop="score" label="AI评分" width="80">
          <template #default="{ row }">{{ row.score != null ? Math.round(row.score) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="teacher_score" label="教师评分" width="90">
          <template #default="{ row }">{{ row.teacher_score != null ? Math.round(row.teacher_score) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusTag(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="120">
          <template #default="{ row }">{{ row.submitted_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openReview(row)">点评</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="store.submissions.length === 0" description="暂无提交" />
      <template #footer>
        <el-button @click="showSubmissionsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 点评对话框 -->
    <el-dialog v-model="showReviewDialog" title="作业点评" width="480px">
      <el-form label-position="top">
        <el-form-item label="教师评分">
          <el-input-number v-model="reviewForm.teacher_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="评语">
          <el-input v-model="reviewForm.teacher_feedback" type="textarea" :rows="4" placeholder="给学生写评语..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReview" :loading="loading">提交点评</el-button>
      </template>
    </el-dialog>
  </div>
</template>