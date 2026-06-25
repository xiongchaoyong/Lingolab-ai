<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const store = useAdminStore()
const loading = ref(false)

const searchQuery = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

onMounted(() => {
  loadUsers()
})

function loadUsers() {
  loading.value = true
  store.fetchUsers({
    page: currentPage.value,
    page_size: pageSize.value,
    search: searchQuery.value,
    role: filterRole.value,
  }).finally(() => {
    loading.value = false
  })
}

let searchTimer = null
watch([searchQuery, filterRole], () => {
  clearTimeout(searchTimer)
  currentPage.value = 1
  searchTimer = setTimeout(loadUsers, 300)
})

watch([currentPage, pageSize], () => {
  loadUsers()
})

async function toggleStatus(user) {
  const newStatus = user.is_active ? 0 : 1
  const action = newStatus ? '启用' : '禁用'
  try {
    await store.setUserStatus(user.id, newStatus)
    user.is_active = newStatus
    ElMessage.success(`${action}成功`)
  } catch (e) {
    ElMessage.error(`${action}失败`)
  }
}

function getRoleTag(role) {
  const map = { admin: 'danger', teacher: 'warning', learner: 'info' }
  return map[role] || 'info'
}

function getRoleLabel(role) {
  const map = { admin: '管理员', teacher: '教师', learner: '学生' }
  return map[role] || role
}

function getLevelTag(level) {
  if (!level) return 'info'
  if (level.startsWith('A')) return 'success'
  if (level.startsWith('B')) return 'warning'
  if (level.startsWith('C')) return 'danger'
  return 'info'
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">用户管理</h2>

    <div class="filter-bar">
      <el-input v-model="searchQuery" placeholder="搜索用户名" :prefix-icon="Search" style="width:240px" clearable />
      <el-select v-model="filterRole" placeholder="角色筛选" style="width:140px" clearable>
        <el-option label="学生" value="learner" />
        <el-option label="教师" value="teacher" />
        <el-option label="管理员" value="admin" />
      </el-select>
    </div>

    <el-table :data="store.users" stripe v-loading="loading">
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="getRoleTag(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="level_final" label="CEFR" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="getLevelTag(row.level_final)">{{ row.level_final || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_minutes" label="学习时长" width="100">
        <template #default="{ row }">{{ Math.floor(row.total_minutes / 60) }}h</template>
      </el-table-column>
      <el-table-column prop="assessment_completed" label="测评" width="70">
        <template #default="{ row }">
          <el-tag size="small" :type="row.assessment_completed ? 'success' : 'info'">
            {{ row.assessment_completed ? '已完成' : '未测' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '活跃' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="120">
        <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button
            size="small" text
            :type="row.is_active ? 'danger' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top:var(--spacing-lg);text-align:right;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="store.userTotal"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        small
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.filter-bar {
  display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg);
}
</style>