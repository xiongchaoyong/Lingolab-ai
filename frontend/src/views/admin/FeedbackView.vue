<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFeedbacksApi, replyFeedbackApi, resolveFeedbackApi } from '@/api/admin'

const feedbacks = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

const typeMap = {
  bug: 'Bug反馈',
  feature: '功能建议',
  scene: '场景建议',
  other: '其他',
}
const statusMap = { pending: 'info', resolved: 'success' }
const statusLabel = { pending: '待处理', resolved: '已解决' }

const showReplyDialog = ref(false)
const selectedFeedback = ref(null)
const replyText = ref('')
const replyLoading = ref(false)

onMounted(() => { loadFeedbacks() })

async function loadFeedbacks() {
  loading.value = true
  try {
    const res = await getFeedbacksApi({ page: page.value, page_size: pageSize.value, status: statusFilter.value })
    feedbacks.value = res.feedbacks || []
    total.value = res.total || 0
  } catch {
    ElMessage.error('加载反馈列表失败')
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  page.value = 1
  loadFeedbacks()
}

function openReply(fb) {
  selectedFeedback.value = fb
  replyText.value = ''
  showReplyDialog.value = true
}

async function submitReply() {
  if (!replyText.value) return
  replyLoading.value = true
  try {
    await replyFeedbackApi(selectedFeedback.value.id, replyText.value)
    ElMessage.success('回复成功')
    showReplyDialog.value = false
    loadFeedbacks()
  } catch {
    ElMessage.error('回复失败')
  } finally {
    replyLoading.value = false
  }
}

async function handleResolve(fb) {
  try {
    await resolveFeedbackApi(fb.id)
    ElMessage.success('已标记解决')
    loadFeedbacks()
  } catch {
    ElMessage.error('操作失败')
  }
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">反馈管理</h2>
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px;" @change="handleFilterChange">
        <el-option label="待处理" value="pending" />
        <el-option label="已解决" value="resolved" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="feedbacks" stripe empty-text="暂无反馈数据">
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="content" label="反馈内容" min-width="260" />
      <el-table-column prop="feedback_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ typeMap[row.feedback_type] || row.feedback_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="120">
        <template #default="{ row }">{{ row.created_at ? new Date(row.created_at).toLocaleDateString('zh-CN') : '' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="statusMap[row.status]">{{ statusLabel[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openReply(row)" v-if="row.status === 'pending'">回复</el-button>
          <el-button size="small" text type="success" @click="handleResolve(row)" v-if="row.status === 'pending'">标记解决</el-button>
          <span v-else style="color: var(--color-text-disabled); font-size: var(--font-size-sm);">已处理</span>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="total > pageSize" style="margin-top: var(--spacing-lg); display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadFeedbacks"
      />
    </div>

    <el-dialog v-model="showReplyDialog" title="回复反馈" width="440px">
      <p style="margin-bottom: var(--spacing-md); color: var(--color-text-secondary);">
        用户 {{ selectedFeedback?.username }}：{{ selectedFeedback?.content }}
      </p>
      <el-input v-model="replyText" type="textarea" :rows="4" placeholder="输入回复内容..." />
      <template #footer>
        <el-button @click="showReplyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReply" :disabled="!replyText" :loading="replyLoading">回复并标记解决</el-button>
      </template>
    </el-dialog>
  </div>
</template>
