<script setup>
import { ref } from 'vue'

const feedbacks = ref([
  { id: 1, user: 'Alice', content: '发音评分有时候不太准确，希望能改进', type: '功能建议', status: 'pending', createdAt: '6月3日' },
  { id: 2, user: 'Bob', content: '对话场景希望能增加酒店入住', type: '场景建议', status: 'pending', createdAt: '6月2日' },
  { id: 3, user: 'Charlie', content: '录音按钮有时没有反应', type: 'Bug反馈', status: 'resolved', createdAt: '6月1日' },
])

const showReplyDialog = ref(false)
const selectedFeedback = ref(null)
const replyText = ref('')

function openReply(fb) {
  selectedFeedback.value = fb
  replyText.value = ''
  showReplyDialog.value = true
}

function submitReply() {
  selectedFeedback.value.status = 'resolved'
  showReplyDialog.value = false
}

function resolveFeedback(fb) {
  fb.status = 'resolved'
}

const statusMap = { pending: 'info', resolved: 'success' }
const statusLabel = { pending: '待处理', resolved: '已解决' }
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">反馈管理</h2>

    <el-table :data="feedbacks" stripe>
      <el-table-column prop="user" label="用户" width="100" />
      <el-table-column prop="content" label="反馈内容" min-width="260" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }"><el-tag size="small" effect="plain">{{ row.type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="createdAt" label="时间" width="80" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="statusMap[row.status]">{{ statusLabel[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openReply(row)" v-if="row.status === 'pending'">回复</el-button>
          <el-button size="small" text type="success" @click="resolveFeedback(row)" v-if="row.status === 'pending'">标记解决</el-button>
          <span v-else style="color: var(--color-text-disabled); font-size: var(--font-size-sm);">已处理</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showReplyDialog" title="回复反馈" width="440px">
      <p style="margin-bottom: var(--spacing-md); color: var(--color-text-secondary);">
        用户 {{ selectedFeedback?.user }}：{{ selectedFeedback?.content }}
      </p>
      <el-input v-model="replyText" type="textarea" :rows="4" placeholder="输入回复内容..." />
      <template #footer>
        <el-button @click="showReplyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReply" :disabled="!replyText">回复并标记解决</el-button>
      </template>
    </el-dialog>
  </div>
</template>
