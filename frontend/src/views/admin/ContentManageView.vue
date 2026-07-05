<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { getContentListApi, createContentApi, updateContentApi, deleteContentApi } from '@/api/admin'

const activeTab = ref('questions')
const loading = ref(false)
const saving = ref(false)

const contentData = ref({
  questions: [],
  shadow: [],
  materials: [],
  dubbing: [],
})

// 分页状态（每种内容类型独立）
const pagination = ref({
  questions: { page: 1, total: 0 },
  shadow: { page: 1, total: 0 },
  materials: { page: 1, total: 0 },
  dubbing: { page: 1, total: 0 },
})
const pageSize = 10

const tabs = [
  { name: 'questions', label: '测评题库' },
  { name: 'shadow', label: '跟读内容' },
  { name: 'materials', label: '推荐资料' },
  { name: 'dubbing', label: '配音片段' },
]

const columns = {
  questions: [
    { prop: 'content', label: '题目内容' },
    { prop: 'type', label: '题型', width: 80 },
    { prop: 'difficulty', label: '难度', width: 70 },
    { prop: 'dimension', label: '维度', width: 70 },
  ],
  shadow: [
    { prop: 'word', label: '内容' },
    { prop: 'ipa', label: '音标', width: 150 },
    { prop: 'difficulty', label: '难度', width: 70 },
    { prop: 'type', label: '类型', width: 70 },
  ],
  materials: [
    { prop: 'title', label: '标题' },
    { prop: 'type', label: '类型', width: 80 },
    { prop: 'category', label: '标签', width: 80 },
    { prop: 'level', label: '等级', width: 70 },
  ],
  dubbing: [
    { prop: 'title', label: '来源' },
    { prop: 'line', label: '台词' },
    { prop: 'difficulty', label: '难度', width: 80 },
  ],
}

const formFields = {
  questions: [
    { key: 'content', label: '题目内容', type: 'textarea', required: true },
    { key: 'type', label: '题型', type: 'select', options: ['speaking', 'reading', 'grammar'], required: true },
    { key: 'difficulty', label: '难度', type: 'select', options: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'], required: true },
    { key: 'dimension', label: '维度', type: 'select', options: ['speaking', 'reading', 'grammar'], required: true },
  ],
  shadow: [
    { key: 'word', label: '文本内容', type: 'textarea', required: true },
    { key: 'ipa', label: '音标', type: 'input' },
    { key: 'difficulty', label: '难度', type: 'select', options: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'], required: true },
    { key: 'type', label: '类型', type: 'select', options: ['word', 'sentence'], required: true },
  ],
  materials: [
    { key: 'title', label: '标题', type: 'input', required: true },
    { key: 'type', label: '类型', type: 'select', options: ['video', 'article', 'audio'], required: true },
    { key: 'level', label: '等级', type: 'select', options: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'], required: true },
    { key: 'category', label: '分类', type: 'input' },
    { key: 'description', label: '描述', type: 'textarea' },
  ],
  dubbing: [
    { key: 'title', label: '来源', type: 'input', required: true },
    { key: 'line', label: '台词', type: 'textarea', required: true },
    { key: 'difficulty', label: '难度', type: 'select', options: ['easy', 'medium', 'hard'], required: true },
  ],
}

const showDialog = ref(false)
const dialogMode = ref('create')
const editingItem = ref(null)
const formData = ref({})

const dialogTitle = computed(() => dialogMode.value === 'create' ? '新增内容' : '编辑内容')
const currentFields = computed(() => formFields[activeTab.value] || [])

onMounted(() => { loadContent(activeTab.value) })
watch(activeTab, (tab) => { loadContent(tab) })

async function loadContent(type) {
  loading.value = true
  const pg = pagination.value[type]
  try {
    const res = await getContentListApi(type, { page: pg.page, page_size: pageSize })
    contentData.value[type] = res.items || []
    pg.total = res.total || 0
  } catch {
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(type, page) {
  pagination.value[type].page = page
  loadContent(type)
}

function openCreate() {
  dialogMode.value = 'create'
  editingItem.value = null
  formData.value = {}
  currentFields.value.forEach(f => {
    formData.value[f.key] = ''
  })
  showDialog.value = true
}

function openEdit(row) {
  dialogMode.value = 'edit'
  editingItem.value = row
  formData.value = { ...row }
  showDialog.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const type = activeTab.value
    if (dialogMode.value === 'create') {
      await createContentApi({ content_type: type, data: formData.value })
      ElMessage.success('创建成功')
    } else {
      await updateContentApi(type, editingItem.value.id, formData.value)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    // 重置页码并重新加载
    pagination.value[type].page = 1
    await loadContent(type)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该内容吗？', '确认删除', { type: 'warning' })
  } catch {
    return
  }
  saving.value = true
  try {
    await deleteContentApi(activeTab.value, row.id)
    ElMessage.success('删除成功')
    // 如果当前页只剩一条且不是第一页，回退一页
    const pg = pagination.value[activeTab.value]
    if (contentData.value[activeTab.value].length === 1 && pg.page > 1) {
      pg.page -= 1
    }
    await loadContent(activeTab.value)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">内容管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name">
        <el-table v-loading="loading" :data="contentData[tab.name]" stripe empty-text="暂无数据">
          <el-table-column
            v-for="col in columns[tab.name]"
            :key="col.prop"
            :prop="col.prop"
            :label="col.label"
            :width="col.width"
          >
            <template v-if="col.prop === 'difficulty'" #default="{ row }">
              <el-tag size="small">{{ row.difficulty }}</el-tag>
            </template>
            <template v-else-if="col.prop === 'type'" #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap" v-if="pagination[tab.name].total > pageSize">
          <el-pagination
            :current-page="pagination[tab.name].page"
            :page-size="pageSize"
            :total="pagination[tab.name].total"
            layout="prev, pager, next"
            @current-change="(p) => handlePageChange(tab.name, p)"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item
          v-for="field in currentFields"
          :key="field.key"
          :label="field.label"
          :required="field.required"
        >
          <el-input v-if="field.type === 'input'" v-model="formData[field.key]" />
          <el-input v-else-if="field.type === 'textarea'" v-model="formData[field.key]" type="textarea" :rows="3" />
          <el-select v-else-if="field.type === 'select'" v-model="formData[field.key]" style="width: 100%">
            <el-option v-for="opt in field.options" :key="opt" :label="opt" :value="opt" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-lg);
}
</style>
