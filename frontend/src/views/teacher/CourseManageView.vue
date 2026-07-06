<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const courses = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增课程')
const isEdit = ref(false)

const defaultForm = () => ({
  id: null,
  title: '',
  description: '',
  level: 'B1',
  unit_count: 4,
  status: 'draft',
})

const form = reactive(defaultForm())

const levelOptions = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
const statusMap = { draft: '草稿', published: '已发布', archived: '已归档' }

onMounted(() => { loadCourses() })

function loadCourses() {
  loading.value = true
  // 模拟数据 — 后续对接后端 API
  setTimeout(() => {
    courses.value = [
      { id: 1, title: '英语发音基础', description: '元音与辅音发音技巧', level: 'A1', unit_count: 6, status: 'published', student_count: 32, created_at: '2026-06-01' },
      { id: 2, title: '日常情景对话', description: '购物、餐厅、旅行等场景', level: 'A2', unit_count: 8, status: 'published', student_count: 28, created_at: '2026-06-10' },
      { id: 3, title: '商务英语进阶', description: '会议、邮件、谈判技巧', level: 'B2', unit_count: 10, status: 'draft', student_count: 0, created_at: '2026-06-20' },
      { id: 4, title: '雅思口语专项', description: 'Part 1-3 话题训练', level: 'C1', unit_count: 12, status: 'draft', student_count: 0, created_at: '2026-07-01' },
    ]
    loading.value = false
  }, 300)
}

function openCreate() {
  isEdit.value = false
  dialogTitle.value = '新增课程'
  Object.assign(form, defaultForm())
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  dialogTitle.value = '编辑课程'
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除课程「${row.title}」吗？`, '确认删除', { type: 'warning' })
    courses.value = courses.value.filter(c => c.id !== row.id)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

function handleSave() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入课程名称')
    return
  }
  if (isEdit.value) {
    const idx = courses.value.findIndex(c => c.id === form.id)
    if (idx > -1) courses.value[idx] = { ...form }
    ElMessage.success('已更新')
  } else {
    courses.value.push({ ...form, id: Date.now(), student_count: 0, created_at: new Date().toISOString().slice(0, 10) })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
}

function getStatusTag(status) {
  const map = { draft: 'info', published: 'success', archived: 'warning' }
  return map[status] || 'info'
}
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <div>
        <h2 class="page-title">课程管理</h2>
        <p class="page-sub">管理教学课程与学习单元</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增课程</el-button>
    </div>

    <el-table :data="courses" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="title" label="课程名称" min-width="160" />
      <el-table-column prop="description" label="课程描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="level" label="等级" width="80" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="primary">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="unit_count" label="单元数" width="80" align="center" />
      <el-table-column prop="student_count" label="学习人数" width="90" align="center" />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="getStatusTag(row.status)">{{ statusMap[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建日期" width="120" align="center" />
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="课程名称" required>
          <el-input v-model="form.title" placeholder="请输入课程名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="课程描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="课程简介" maxlength="200" />
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="form.level" style="width: 100%">
            <el-option v-for="lv in levelOptions" :key="lv" :label="lv" :value="lv" />
          </el-select>
        </el-form-item>
        <el-form-item label="单元数量">
          <el-input-number v-model="form.unit_count" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">已发布</el-radio>
            <el-radio value="archived">已归档</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
