<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyClassesApi } from '@/api/student'
import { joinClassApi } from '@/api/admin'

const classes = ref([])
const loading = ref(false)
const showJoinDialog = ref(false)
const inviteCode = ref('')
const joining = ref(false)

onMounted(() => { loadClasses() })

async function loadClasses() {
  loading.value = true
  try {
    const res = await getMyClassesApi()
    classes.value = res.classes || []
  } catch {
    ElMessage.error('加载班级列表失败')
  } finally {
    loading.value = false
  }
}

async function handleJoin() {
  if (!inviteCode.value) return
  joining.value = true
  try {
    await joinClassApi(inviteCode.value)
    ElMessage.success('加入班级成功')
    showJoinDialog.value = false
    inviteCode.value = ''
    await loadClasses()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加入失败')
  } finally {
    joining.value = false
  }
}
</script>

<template>
  <div class="content-card classes-page">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">我的班级</h2>
      <el-button type="primary" @click="showJoinDialog = true">加入班级</el-button>
    </div>

    <div class="classes-table-wrap">
      <el-table v-loading="loading" :data="classes" stripe height="100%">
        <el-table-column prop="name" label="班级名称" min-width="160" />
        <el-table-column prop="teacher_name" label="教师" width="120" />
        <el-table-column prop="level_range" label="等级范围" width="100">
          <template #default="{ row }">
            <el-tag size="small" v-if="row.level_range">{{ row.level_range }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="student_count" label="学生数" width="80" />
        <el-table-column prop="joined_at" label="加入时间" width="120">
          <template #default="{ row }">{{ row.joined_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-if="!loading && classes.length === 0" description="暂未加入任何班级，点击上方按钮通过邀请码加入" />

    <!-- 加入班级对话框 -->
    <el-dialog v-model="showJoinDialog" title="加入班级" width="400px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="邀请码">
          <el-input v-model="inviteCode" placeholder="输入教师提供的邀请码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showJoinDialog = false">取消</el-button>
        <el-button type="primary" @click="handleJoin" :disabled="!inviteCode" :loading="joining">加入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.classes-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - var(--spacing-xl) * 2);
}

.classes-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>