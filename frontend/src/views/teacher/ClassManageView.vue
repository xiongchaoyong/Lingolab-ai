<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import { refreshInviteCodeApi } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useAdminStore()

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showStudentsDialog = ref(false)
const showJoinDialog = ref(false)
const newClass = ref({ name: '', description: '', level_range: 'A1-A2' })
const editClass = ref({ id: null, name: '', description: '', level_range: '' })
const inviteCode = ref('')
const loading = ref(false)
const viewingClass = ref(null)

onMounted(() => {
  store.fetchClasses()
})

async function createClass() {
  if (!newClass.value.name) return
  loading.value = true
  try {
    await store.createClass({
      name: newClass.value.name,
      description: newClass.value.description,
      level_range: newClass.value.level_range,
    })
    ElMessage.success('班级创建成功')
    showCreateDialog.value = false
    newClass.value = { name: '', description: '', level_range: 'A1-A2' }
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    loading.value = false
  }
}

function openEditDialog(cls) {
  editClass.value = {
    id: cls.id,
    name: cls.name,
    description: cls.description || '',
    level_range: cls.level_range || '',
  }
  showEditDialog.value = true
}

async function submitEdit() {
  if (!editClass.value.name) return
  loading.value = true
  try {
    await store.updateClass(editClass.value.id, {
      name: editClass.value.name,
      description: editClass.value.description,
      level_range: editClass.value.level_range,
    })
    ElMessage.success('班级信息已更新')
    showEditDialog.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally {
    loading.value = false
  }
}

async function deleteClass(cls) {
  try {
    await ElMessageBox.confirm(
      `确定要删除班级「${cls.name}」吗？此操作将停用班级，已有学生数据不会丢失。`,
      '确认删除',
      { type: 'warning' }
    )
  } catch { return }
  try {
    await store.deleteClass(cls.id)
    ElMessage.success('班级已删除')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function viewStudents(cls) {
  viewingClass.value = cls
  try {
    await store.fetchStudents(cls.id)
    showStudentsDialog.value = true
  } catch (e) {
    ElMessage.error('获取学生列表失败')
  }
}

async function removeStudent(user) {
  try {
    await ElMessageBox.confirm(`确定要将「${user.username}」移出班级吗？`, '确认移除', { type: 'warning' })
  } catch { return }
  try {
    await store.removeStudent(viewingClass.value.id, user.id)
    ElMessage.success(`${user.username} 已移出班级`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '移除失败')
  }
}

async function joinClass() {
  if (!inviteCode.value) return
  loading.value = true
  try {
    await store.joinClass(inviteCode.value)
    ElMessage.success('加入班级成功')
    showJoinDialog.value = false
    inviteCode.value = ''
    store.fetchClasses()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加入失败')
  } finally {
    loading.value = false
  }
}

async function copyInviteCode(code) {
  await navigator.clipboard.writeText(code)
  ElMessage.success('邀请码已复制')
}

async function refreshInviteCode(cls) {
  try {
    const res = await refreshInviteCodeApi(cls.id)
    cls.invite_code = res.data.invite_code
    ElMessage.success('邀请码已刷新')
  } catch (e) {
    ElMessage.error('刷新失败')
  }
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
  <div class="content-card class-manage-page">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">班级管理</h2>
      <div style="display:flex;gap:var(--spacing-sm);">
        <el-button @click="showJoinDialog = true">加入班级</el-button>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">创建班级</el-button>
      </div>
    </div>

    <div class="class-table-wrap">
      <el-table :data="store.classes" stripe v-loading="loading" height="100%">
      <el-table-column prop="name" label="班级名称" min-width="120" />
      <el-table-column prop="level_range" label="等级范围" width="100">
        <template #default="{ row }">
          <el-tag size="small" v-if="row.level_range">{{ row.level_range }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="student_count" label="学生数" width="80" />
      <el-table-column prop="invite_code" label="邀请码" width="200">
        <template #default="{ row }">
          <el-tag type="success" style="cursor:pointer" @click="copyInviteCode(row.invite_code)">
            {{ row.invite_code }}
          </el-tag>
          <el-button size="small" text type="warning" @click="refreshInviteCode(row)" style="margin-left:4px">刷新</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewStudents(row)">学生</el-button>
          <el-button size="small" text type="warning" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="deleteClass(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-empty v-if="store.classes.length === 0 && !loading" description="暂无班级，创建班级并分享邀请码给学生加入" />

    <!-- 创建班级对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建班级" width="440px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="班级名称">
          <el-input v-model="newClass.name" placeholder="如：初级英语A班" maxlength="100" />
        </el-form-item>
        <el-form-item label="等级范围">
          <el-select v-model="newClass.level_range" style="width:100%">
            <el-option label="A1 - A2 (入门-基础)" value="A1-A2" />
            <el-option label="B1 - B2 (中级-中高级)" value="B1-B2" />
            <el-option label="C1 - C2 (高级-精通)" value="C1-C2" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级描述">
          <el-input v-model="newClass.description" type="textarea" :rows="3" placeholder="班级描述（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createClass" :disabled="!newClass.name" :loading="loading">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑班级对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑班级" width="440px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="班级名称">
          <el-input v-model="editClass.name" placeholder="班级名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="等级范围">
          <el-select v-model="editClass.level_range" style="width:100%">
            <el-option label="A1 - A2 (入门-基础)" value="A1-A2" />
            <el-option label="B1 - B2 (中级-中高级)" value="B1-B2" />
            <el-option label="C1 - C2 (高级-精通)" value="C1-C2" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级描述">
          <el-input v-model="editClass.description" type="textarea" :rows="3" placeholder="班级描述（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :disabled="!editClass.name" :loading="loading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 学生列表对话框 -->
    <el-dialog v-model="showStudentsDialog" title="班级学生" width="600px" :close-on-click-modal="false">
      <el-table :data="store.students" stripe max-height="400">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="level_final" label="CEFR" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getLevelTag(row.level_final)">{{ row.level_final || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_minutes" label="学习时长" width="100">
          <template #default="{ row }">{{ Math.floor(row.total_minutes / 60) }}h</template>
        </el-table-column>
        <el-table-column prop="joined_at" label="加入时间" width="120">
          <template #default="{ row }">{{ row.joined_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="danger" @click="removeStudent(row)">移出</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="store.students.length === 0" description="暂无学生" />
      <template #footer>
        <el-button @click="showStudentsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 加入班级对话框 -->
    <el-dialog v-model="showJoinDialog" title="加入班级" width="400px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="邀请码">
          <el-input v-model="inviteCode" placeholder="输入教师提供的邀请码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showJoinDialog = false">取消</el-button>
        <el-button type="primary" @click="joinClass" :disabled="!inviteCode" :loading="loading">加入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.class-manage-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - var(--spacing-xl) * 2);
}

.class-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
