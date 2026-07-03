<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search, Refresh, Plus, Delete, Edit, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getKnowledgeDocsApi,
  createKnowledgeDocApi,
  updateKnowledgeDocApi,
  deleteKnowledgeDocApi,
  reindexKnowledgeDocApi,
  rebuildKnowledgeIndexApi,
  getSearchLogsApi,
} from '@/api/admin'

// ========== 文档管理状态 ==========
const loading = ref(true)
const docs = ref([])
const docTotal = ref(0)
const docPage = ref(1)
const docPageSize = ref(20)
const docSearch = ref('')
const docCategory = ref('')

// ========== 检索日志状态 ==========
const logLoading = ref(false)
const logs = ref([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(20)

// ========== 文档弹窗 ==========
const dialogVisible = ref(false)
const dialogTitle = ref('新增文档')
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  title: '',
  content: '',
  category: 'general',
})

// ========== 活动标签页 ==========
const activeTab = ref('docs')

const categoryOptions = [
  { value: 'product_use', label: '产品使用' },
  { value: 'study_advice', label: '学习建议' },
  { value: 'tech_issue', label: '技术问题' },
  { value: 'refund', label: '退款相关' },
  { value: 'general', label: '通用' },
]

function getCategoryLabel(cat) {
  const opt = categoryOptions.find(o => o.value === cat)
  return opt ? opt.label : cat
}

function getCategoryTag(cat) {
  const map = { product_use: 'success', study_advice: 'warning', tech_issue: 'danger', refund: 'info', general: '' }
  return map[cat] || ''
}

// ========== 文档列表 ==========
async function loadDocs() {
  loading.value = true
  try {
    const res = await getKnowledgeDocsApi({
      page: docPage.value,
      page_size: docPageSize.value,
      search: docSearch.value,
      category: docCategory.value,
    })
    docs.value = res.items || []
    docTotal.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

let fetchTimer = null

// 搜索/分类变化：重置页码 + 防抖加载（避免连续输入时频繁请求）
watch([docSearch, docCategory], () => {
  docPage.value = 1
  clearTimeout(fetchTimer)
  fetchTimer = setTimeout(loadDocs, 300)
})

// 翻页/页大小变化：立即加载，同时取消防抖队列中待执行的请求
watch([docPage, docPageSize], () => {
  clearTimeout(fetchTimer)
  loadDocs()
})

onMounted(() => {
  loadDocs()
})

// ========== 文档 CRUD ==========
function openCreateDialog() {
  dialogTitle.value = '新增文档'
  isEditing.value = false
  editingId.value = null
  formData.value = { title: '', content: '', category: 'general' }
  dialogVisible.value = true
}

function openEditDialog(doc) {
  dialogTitle.value = '编辑文档'
  isEditing.value = true
  editingId.value = doc.id
  formData.value = {
    title: doc.title,
    content: doc.content,
    category: doc.category,
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.value.title.trim() || !formData.value.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  try {
    if (isEditing.value) {
      await updateKnowledgeDocApi(editingId.value, formData.value)
      ElMessage.success('更新成功')
    } else {
      await createKnowledgeDocApi(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadDocs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function deleteDoc(doc) {
  try {
    await ElMessageBox.confirm(`确定要删除文档「${doc.title}」吗？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await deleteKnowledgeDocApi(doc.id)
    ElMessage.success('删除成功')
    loadDocs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function reindexDoc(doc) {
  try {
    await reindexKnowledgeDocApi(doc.id)
    ElMessage.success('重新索引成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '索引失败')
  }
}

async function rebuildAll() {
  try {
    await ElMessageBox.confirm('确定要全量重建向量索引吗？这将清空现有索引并重新构建。', '确认操作', { type: 'warning' })
  } catch { return }
  try {
    const res = await rebuildKnowledgeIndexApi()
    ElMessage.success(res.message || '全量重建完成')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '重建失败')
  }
}

// ========== 检索日志 ==========
async function loadLogs() {
  logLoading.value = true
  try {
    const res = await getSearchLogsApi({
      page: logPage.value,
      page_size: logPageSize.value,
    })
    logs.value = res.items || []
    logTotal.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载检索日志失败')
  } finally {
    logLoading.value = false
  }
}

function onTabChange(tab) {
  if (tab === 'logs' && logs.value.length === 0) {
    loadLogs()
  }
}

watch([logPage, logPageSize], () => {
  if (activeTab.value === 'logs') loadLogs()
})

function formatLogTime(time) {
  if (!time) return ''
  const d = new Date(time)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getRetrievedTitles(log) {
  if (!log.retrieved_docs || !Array.isArray(log.retrieved_docs)) return '-'
  return log.retrieved_docs.map(d => d.title || `#${d.id}`).join('、')
}

function truncateText(text, max = 60) {
  if (!text) return '-'
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">知识库管理</h2>
    <p class="page-desc">管理 RAG 智能客服的文档知识库，维护向量索引，查看检索日志</p>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- ========== 文档管理 ========== -->
      <el-tab-pane label="文档管理" name="docs">
        <div class="toolbar">
          <div class="toolbar-left">
            <el-input
              v-model="docSearch"
              placeholder="搜索文档标题或内容..."
              :prefix-icon="Search"
              clearable
              style="width: 280px"
            />
            <el-select v-model="docCategory" placeholder="分类筛选" clearable style="width: 140px">
              <el-option
                v-for="opt in categoryOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
          <div class="toolbar-right">
            <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增文档</el-button>
            <el-button :icon="Refresh" @click="rebuildAll">全量重建索引</el-button>
          </div>
        </div>

        <!-- 加载占位 — loading 初始为 true，确保表格永远不会在数据就绪前渲染 -->
        <div v-if="loading" style="text-align:center;padding:80px 0;">
          <el-icon class="is-loading" :size="36" color="var(--color-primary)"><Loading /></el-icon>
          <p style="margin-top:12px;color:var(--color-text-secondary);">加载中...</p>
        </div>

        <el-table v-else :data="docs" stripe style="width: 100%; margin-top: 16px">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="content" label="内容摘要" min-width="280" show-overflow-tooltip>
            <template #default="{ row }">{{ truncateText(row.content, 80) }}</template>
          </el-table-column>
          <el-table-column label="分类" width="110">
            <template #default="{ row }">
              <el-tag :type="getCategoryTag(row.category)" size="small">
                {{ getCategoryLabel(row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源" width="80">
            <template #default="{ row }">
              <el-tag :type="row.source_type === 'faq' ? 'warning' : ''" size="small" effect="plain">
                {{ row.source_type === 'faq' ? 'FAQ' : '手动' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="170">
            <template #default="{ row }">{{ formatLogTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" :icon="Edit" @click="openEditDialog(row)">编辑</el-button>
              <el-button size="small" :icon="Refresh" @click="reindexDoc(row)">索引</el-button>
              <el-button size="small" :icon="Delete" type="danger" @click="deleteDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="docTotal > docPageSize"
          style="margin-top: 16px; justify-content: flex-end"
          v-model:current-page="docPage"
          v-model:page-size="docPageSize"
          :total="docTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
        />
      </el-tab-pane>

      <!-- ========== 检索日志 ========== -->
      <el-tab-pane label="检索日志" name="logs">
        <el-table :data="logs" v-loading="logLoading" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="query" label="用户提问" min-width="200" show-overflow-tooltip />
          <el-table-column prop="username" label="用户" width="100">
            <template #default="{ row }">{{ row.username || '访客' }}</template>
          </el-table-column>
          <el-table-column label="检索结果" min-width="200">
            <template #default="{ row }">{{ getRetrievedTitles(row) }}</template>
          </el-table-column>
          <el-table-column label="AI回复" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">{{ truncateText(row.reply, 80) }}</template>
          </el-table-column>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatLogTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="logTotal > logPageSize"
          style="margin-top: 16px; justify-content: flex-end"
          v-model:current-page="logPage"
          v-model:page-size="logPageSize"
          :total="logTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- ========== 新增/编辑文档弹窗 ========== -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px" destroy-on-close>
      <el-form :model="formData" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="formData.title" placeholder="文档标题（如常见问题）" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="formData.category" style="width: 100%">
            <el-option
              v-for="opt in categoryOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="8"
            placeholder="文档正文内容，支持 Markdown 格式"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.content-card {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.page-desc {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  margin: 0 0 20px 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
