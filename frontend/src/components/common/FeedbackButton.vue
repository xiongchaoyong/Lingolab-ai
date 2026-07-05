<script setup>
import { ref } from 'vue'
import { ChatLineSquare } from '@element-plus/icons-vue'
import { submitFeedbackApi } from '@/api/admin'
import { ElMessage } from 'element-plus'

const dialogVisible = ref(false)
const content = ref('')
const feedbackType = ref('feature')
const submitting = ref(false)

const typeOptions = [
  { value: 'feature', label: '功能建议' },
  { value: 'bug', label: 'Bug反馈' },
  { value: 'scene', label: '场景建议' },
  { value: 'other', label: '其他' },
]

function typeLabel(value) {
  return typeOptions.find(t => t.value === value)?.label || value
}

async function submit() {
  if (!content.value.trim()) return
  submitting.value = true
  try {
    await submitFeedbackApi(content.value.trim(), feedbackType.value)
    ElMessage.success('感谢你的反馈，我们会尽快处理！')
    dialogVisible.value = false
    content.value = ''
    feedbackType.value = 'feature'
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="feedback-fab">
    <el-tooltip content="提交反馈" placement="left">
      <button class="fab-btn" @click="dialogVisible = true">
        <el-icon :size="20"><ChatLineSquare /></el-icon>
      </button>
    </el-tooltip>

    <el-dialog
      v-model="dialogVisible"
      title="提交反馈"
      width="440px"
      :close-on-click-modal="false"
      destroy-on-close
      align-center
    >
      <div class="feedback-form">
        <div class="form-item">
          <label>反馈类型</label>
          <el-radio-group v-model="feedbackType" size="small">
            <el-radio-button
              v-for="t in typeOptions" :key="t.value" :value="t.value"
            >{{ t.label }}</el-radio-button>
          </el-radio-group>
        </div>
        <div class="form-item">
          <label>反馈内容</label>
          <el-input
            v-model="content"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="请详细描述你的建议或遇到的问题..."
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!content.trim()" @click="submit">
          提交反馈
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.feedback-fab {
  position: fixed;
  right: 24px;
  bottom: 80px;
  z-index: 999;
}

.fab-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.2s;
  color: var(--color-text-secondary);

  &:hover {
    transform: scale(1.08);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}

.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;

  label {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-secondary);
  }
}
</style>
