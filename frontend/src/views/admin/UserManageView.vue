<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

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

// ========== 状态切换 ==========
async function toggleStatus(user) {
  const newStatus = user.is_active ? 0 : 1
  const action = newStatus ? '启用' : '禁用'
  if (!newStatus) {
    try {
      await ElMessageBox.confirm(`确定要禁用用户「${user.username}」吗？`, '确认操作', { type: 'warning' })
    } catch { return }
  }
  try {
    await store.setUserStatus(user.id, newStatus)
    user.is_active = newStatus
    ElMessage.success(`${action}成功`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || `${action}失败`)
  }
}

// ========== 角色切换 ==========
async function changeRole(user, newRole) {
  const roleLabel = { learner: '学生', teacher: '教师', admin: '管理员' }
  try {
    await ElMessageBox.confirm(
      `确定将「${user.username}」的角色从「${getRoleLabel(user.role)}」改为「${roleLabel[newRole]}」吗？`,
      '确认变更角色',
      { type: 'warning' }
    )
  } catch { return }
  try {
    await store.setUserRole(user.id, newRole)
    user.role = newRole
    ElMessage.success(`角色已更新为 ${roleLabel[newRole]}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '角色变更失败')
  }
}

// ========== 用户详情 ==========
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailUser = ref(null)

async function viewDetail(user) {
  detailVisible.value = true
  detailLoading.value = true
  detailUser.value = null
  try {
    detailUser.value = await store.fetchUserDetail(user.id)
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '获取用户详情失败'
    ElMessage.error(msg)
  } finally {
    detailLoading.value = false
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

function getDimLabel(dim) {
  const map = {
    pronunciation: '发音', fluency: '流利度', grammar: '语法',
    vocabulary: '词汇', comprehension: '理解', overall: '综合',
  }
  return map[dim] || dim
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
      <el-table-column prop="username" label="用户名" width="120" />
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
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewDetail(row)">详情</el-button>
          <el-dropdown trigger="click" @command="(role) => changeRole(row, role)" style="margin:0 4px">
            <el-button size="small" text type="warning">
              角色<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="r in [{k:'learner',v:'学生'},{k:'teacher',v:'教师'},{k:'admin',v:'管理员'}]"
                  :key="r.k"
                  :command="r.k"
                  :disabled="row.role === r.k"
                >
                  {{ r.v }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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

    <!-- ========== 用户详情弹窗 ========== -->
    <el-dialog v-model="detailVisible" title="用户详情" width="560px" destroy-on-close>
      <div v-if="detailLoading" style="text-align:center;padding:40px 0;">
        <span class="kb-spinner" />
        <p style="margin-top:12px;color:var(--color-text-secondary);">加载中...</p>
      </div>
      <div v-else-if="detailUser" class="user-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="ID">{{ detailUser.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ detailUser.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag size="small" :type="getRoleTag(detailUser.role)">{{ getRoleLabel(detailUser.role) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="年龄段">{{ detailUser.age_group || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学习目标">{{ detailUser.learning_goal || '-' }}</el-descriptions-item>
          <el-descriptions-item label="自评等级">{{ detailUser.level_self || '-' }}</el-descriptions-item>
          <el-descriptions-item label="测评等级">
            <el-tag size="small" :type="getLevelTag(detailUser.level_final)">{{ detailUser.level_final || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="small" :type="detailUser.is_active ? 'success' : 'danger'">
              {{ detailUser.is_active ? '活跃' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="测评完成">
            <el-tag size="small" :type="detailUser.assessment_completed ? 'success' : 'info'">
              {{ detailUser.assessment_completed ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总积分">{{ detailUser.total_points }}</el-descriptions-item>
          <el-descriptions-item label="对话次数">{{ detailUser.conversation_count }}</el-descriptions-item>
          <el-descriptions-item label="发音练习">{{ detailUser.pronunciation_count }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ (detailUser.created_at || '').slice(0, 10) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="Object.keys(detailUser.dimension_averages || {}).length" class="detail-scores">
          <h4>维度平均分</h4>
          <div class="dim-tags">
            <el-tag
              v-for="(score, dim) in detailUser.dimension_averages"
              :key="dim"
              size="small"
              effect="plain"
            >
              {{ getDimLabel(dim) }}：{{ score }}
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.filter-bar {
  display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg);
}

.user-detail {
  .detail-scores {
    margin-top: var(--spacing-lg);

    h4 {
      margin: 0 0 var(--spacing-sm) 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }

    .dim-tags {
      display: flex; flex-wrap: wrap; gap: 8px;
    }
  }
}
</style>
