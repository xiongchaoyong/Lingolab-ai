<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyAssignmentsApi, submitAssignmentApi } from '@/api/student'

const assignments = ref([])
const loading = ref(false)
const showSubmitDialog = ref(false)
const currentAssignment = ref(null)
const audioUrl = ref('')
const submitting = ref(false)

onMounted(() => { loadAssignments() })

async function loadAssignments() {
  loading.value = true
  try {
    const res = await getMyAssignmentsApi()
    assignments.value = res.assignments || []
  } catch {
    ElMessage.error('加载作业列表失败')
  } finally {
    loading.value = false
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
  <div class="content-card homework-page">
    <h2 class="page-title">我的作业</h2>

    <div class="homework-table-wrap">
      <el-table v-loading="loading" :data="assignments" stripe height="100%">
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

    <el-empty v-if="!loading && assignments.length === 0" description="暂无作业" />

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
.homework-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - var(--spacing-xl) * 2);
}

.homework-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>