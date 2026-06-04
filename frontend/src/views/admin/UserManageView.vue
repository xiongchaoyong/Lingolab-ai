<script setup>
import { ref } from 'vue'

const searchQuery = ref('')
const filterLevel = ref('')
const filterStatus = ref('')

const users = ref([
  { id: 1, username: 'Alice', level: 'B1', role: 'learner', totalMinutes: 580, status: 'active', registeredAt: '2026-05-20' },
  { id: 2, username: 'Bob', level: 'A2', role: 'learner', totalMinutes: 320, status: 'active', registeredAt: '2026-05-22' },
  { id: 3, username: 'Charlie', level: 'B2', role: 'learner', totalMinutes: 920, status: 'active', registeredAt: '2026-05-18' },
  { id: 4, username: 'David', level: 'C1', role: 'learner', totalMinutes: 45, status: 'inactive', registeredAt: '2026-06-01' },
  { id: 5, username: 'Teacher_Wang', level: 'C1', role: 'teacher', totalMinutes: 120, status: 'active', registeredAt: '2026-05-15' },
])

function toggleStatus(user) {
  user.status = user.status === 'active' ? 'disabled' : 'active'
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">用户管理</h2>

    <div class="filter-bar">
      <el-input v-model="searchQuery" placeholder="搜索用户名" :prefix-icon="Search" style="width:240px" clearable />
      <el-select v-model="filterLevel" placeholder="CEFR等级" style="width:140px" clearable>
        <el-option v-for="l in ['A1','A2','B1','B2','C1','C2']" :key="l" :label="l" :value="l" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" style="width:120px" clearable>
        <el-option label="活跃" value="active" />
        <el-option label="不活跃" value="inactive" />
        <el-option label="已禁用" value="disabled" />
      </el-select>
    </div>

    <el-table :data="users" stripe>
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="level" label="CEFR" width="70">
        <template #default="{ row }"><el-tag size="small">{{ row.level }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === 'teacher' ? 'warning' : 'info'">{{ row.role === 'teacher' ? '教师' : '学生' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="totalMinutes" label="学习时长" width="100">
        <template #default="{ row }">{{ Math.floor(row.totalMinutes / 60) }}h</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'active' ? 'success' : row.status === 'inactive' ? 'warning' : 'danger'">
            {{ row.status === 'active' ? '活跃' : row.status === 'inactive' ? '不活跃' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="registeredAt" label="注册时间" width="120" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" text type="primary">详情</el-button>
          <el-button size="small" text :type="row.status === 'active' ? 'danger' : 'success'" @click="toggleStatus(row)">
            {{ row.status === 'active' ? '禁用' : '恢复' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style lang="scss" scoped>
.filter-bar {
  display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg);
}
</style>
