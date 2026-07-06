<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)

const form = reactive({
  site_name: 'Lingolab',
  site_slogan: 'AI 驱动的英语口语训练平台',
  maintenance_mode: false,
  enable_assessment: true,
  assessment_cooldown_days: 30,
  point_register: 100,
  point_daily_login: 10,
  point_assessment: 50,
  point_pronunciation: 20,
  point_conversation: 30,
  max_class_size: 30,
  max_homework_per_week: 5,
})

onMounted(() => { loadSettings() })

function loadSettings() {
  loading.value = true
  // 模拟加载 — 后续对接后端 API
  setTimeout(() => { loading.value = false }, 300)
}

function handleSave() {
  ElMessage.success('设置已保存')
}

function handleReset() {
  ElMessage.info('已恢复默认设置')
}
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-sub">管理平台全局配置</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleReset">恢复默认</el-button>
        <el-button type="primary" @click="handleSave">保存设置</el-button>
      </div>
    </div>

    <div v-loading="loading" class="settings-body">
      <el-divider content-position="left">基本配置</el-divider>
      <el-form :model="form" label-width="140px" class="settings-form">
        <el-form-item label="平台名称">
          <el-input v-model="form.site_name" style="max-width: 360px" />
        </el-form-item>
        <el-form-item label="平台标语">
          <el-input v-model="form.site_slogan" style="max-width: 360px" />
        </el-form-item>
        <el-form-item label="维护模式">
          <el-switch v-model="form.maintenance_mode" />
          <span class="form-tip">开启后仅管理员可访问</span>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">评估配置</el-divider>
      <el-form :model="form" label-width="140px" class="settings-form">
        <el-form-item label="启用水平评估">
          <el-switch v-model="form.enable_assessment" />
        </el-form-item>
        <el-form-item label="评估冷却天数">
          <el-input-number v-model="form.assessment_cooldown_days" :min="7" :max="90" />
          <span class="form-tip">用户完成评估后需等待的天数</span>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">积分规则</el-divider>
      <el-form :model="form" label-width="140px" class="settings-form">
        <el-form-item label="注册奖励">
          <el-input-number v-model="form.point_register" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="每日登录">
          <el-input-number v-model="form.point_daily_login" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="完成评估">
          <el-input-number v-model="form.point_assessment" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="发音练习">
          <el-input-number v-model="form.point_pronunciation" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="对话练习">
          <el-input-number v-model="form.point_conversation" :min="0" :max="9999" />
        </el-form-item>
      </el-form>

      <el-divider content-position="left">教学限制</el-divider>
      <el-form :model="form" label-width="140px" class="settings-form">
        <el-form-item label="班级人数上限">
          <el-input-number v-model="form.max_class_size" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="每周作业上限">
          <el-input-number v-model="form.max_homework_per_week" :min="1" :max="20" />
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.settings-body {
  padding-top: var(--spacing-md);
}

.settings-form {
  max-width: 640px;

  :deep(.el-divider) {
    margin: var(--spacing-xl) 0 var(--spacing-lg);
  }
}

.form-tip {
  margin-left: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}
</style>
