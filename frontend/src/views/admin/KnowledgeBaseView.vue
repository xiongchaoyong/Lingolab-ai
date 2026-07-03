<script setup>
import { ref, onMounted } from 'vue'
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

// ========== 文档管理 ==========
const loading = ref(true)
const docs = ref([])
const docTotal = ref(0)
const docPage = ref(1)
const docPageSize = ref(20)
const docSearch = ref('')
const docCategory = ref('')

// ========== 检索日志 ==========
const logLoading = ref(false)
const logs = ref([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(20)

// ========== 弹窗 ==========
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const form = ref({ title: '', content: '', category: 'general' })

// ========== Tab ==========
const activeTab = ref('docs')

const categoryOptions = [
  { value: 'product_use', label: '产品使用', tag: 'success' },
  { value: 'study_advice', label: '学习建议', tag: 'warning' },
  { value: 'tech_issue', label: '技术问题', tag: 'danger' },
  { value: 'refund', label: '退款相关', tag: 'info' },
  { value: 'general', label: '通用', tag: '' },
]
const catMeta = Object.fromEntries(categoryOptions.map(c => [c.value, c]))

// ========== 文档列表加载 ==========
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

let searchTimer = null
function onSearchInput() {
  docPage.value = 1
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadDocs, 300)
}

function onDocPageChange(p) {
  docPage.value = p
  loadDocs()
}

function onDocSizeChange(s) {
  docPageSize.value = s
  docPage.value = 1
  loadDocs()
}

onMounted(() => loadDocs())

// ========== 文档 CRUD ==========
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  form.value = { title: '', content: '', category: 'general' }
  dialogVisible.value = true
}

function openEditDialog(doc) {
  isEditing.value = true
  editingId.value = doc.id
  form.value = {
    title: doc.title,
    content: doc.content,
    category: doc.category,
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  try {
    if (isEditing.value) {
      await updateKnowledgeDocApi(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createKnowledgeDocApi(form.value)
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
    const res = await getSearchLogsApi({ page: logPage.value, page_size: logPageSize.value })
    logs.value = res.items || []
    logTotal.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载检索日志失败')
  } finally {
    logLoading.value = false
  }
}

function onTabChange(tab) {
  if (tab === 'logs' && logs.value.length === 0) loadLogs()
}

function onLogPageChange(p) {
  logPage.value = p
  loadLogs()
}

function onLogSizeChange(s) {
  logPageSize.value = s
  logPage.value = 1
  loadLogs()
}

// ========== 工具函数 ==========
function formatTime(t) {
  if (!t) return '-'
  const d = new Date(t)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function getRetrievedTitles(log) {
  if (!log.retrieved_docs?.length) return '-'
  return log.retrieved_docs.map(d => d.title || `#${d.id}`).join('、')
}

function truncate(text, max = 70) {
  if (!text) return '-'
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="kb-page">
    <h2 class="kb-title">知识库管理</h2>
    <p class="kb-desc">管理 RAG 智能客服的文档知识库，维护向量索引，查看检索日志</p>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- ==================== 文档管理 ==================== -->
      <el-tab-pane label="文档管理" name="docs">
        <!-- 工具栏 -->
        <div class="kb-toolbar">
          <div class="kb-toolbar-left">
            <el-input
              v-model="docSearch"
              placeholder="搜索文档标题或内容..."
              clearable
              style="width: 280px"
              @input="onSearchInput"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="docCategory"
              placeholder="分类筛选"
              clearable
              style="width: 140px"
              @change="onSearchInput"
            >
              <el-option
                v-for="opt in categoryOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
          <div class="kb-toolbar-right">
            <el-button type="primary" @click="openCreateDialog">
              <template #icon><el-icon><Plus /></el-icon></template>
              新增文档
            </el-button>
            <el-button @click="rebuildAll">
              <template #icon><el-icon><Refresh /></el-icon></template>
              全量重建索引
            </el-button>
          </div>
        </div>

        <!-- 加载占位 — 纯 CSS spinner，零外部依赖 -->
        <div v-if="loading" class="kb-loading">
          <span class="kb-spinner" />
          <p>加载中...</p>
        </div>

        <!-- 文档表格 -->
        <el-table v-else :data="docs" stripe class="kb-table">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column label="内容摘要" min-width="280" show-overflow-tooltip>
            <template #default="{ row }">{{ truncate(row.content, 80) }}</template>
          </el-table-column>
          <el-table-column label="分类" width="110">
            <template #default="{ row }">
              <el-tag :type="catMeta[row.category]?.tag || ''" size="small">
                {{ catMeta[row.category]?.label || row.category }}
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
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEditDialog(row)">
                <template #icon><el-icon><Edit /></el-icon></template>
                编辑
              </el-button>
              <el-button size="small" @click="reindexDoc(row)">
                <template #icon><el-icon><Refresh /></el-icon></template>
                索引
              </el-button>
              <el-button size="small" type="danger" @click="deleteDoc(row)">
                <template #icon><el-icon><Delete /></el-icon></template>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="docTotal > docPageSize"
          class="kb-pagination"
          :current-page="docPage"
          :page-size="docPageSize"
          :total="docTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onDocPageChange"
          @size-change="onDocSizeChange"
        />
      </el-tab-pane>

      <!-- ==================== 检索日志 ==================== -->
      <el-tab-pane label="检索日志" name="logs">
        <el-table :data="logs" v-loading="logLoading" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="query" label="用户提问" min-width="200" show-overflow-tooltip />
          <el-table-column prop="username" label="用户" width="100">
            <template #default="{ row }">{{ row.username || '访客' }}</template>
          </el-table-column>
          <el-table-column label="检索结果" min-width="200">
            <template #default="{ row }">{{ getRetrievedTitles(row) }}</template>
          </el-table-column>
          <el-table-column label="AI回复" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">{{ truncate(row.reply, 80) }}</template>
          </el-table-column>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="logTotal > logPageSize"
          class="kb-pagination"
          :current-page="logPage"
          :page-size="logPageSize"
          :total="logTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onLogPageChange"
          @size-change="onLogSizeChange"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- ==================== 新增/编辑弹窗 ==================== -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑文档' : '新增文档'" width="640px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="文档标题" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="opt in categoryOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="文档正文内容，支持 Markdown 格式" />
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
.kb-page {
  max-width: 1200px;
  margin: 0 auto;
}

.kb-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.kb-desc {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  margin: 0 0 20px 0;
}

.kb-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.kb-toolbar-left,
.kb-toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-table {
  width: 100%;
  margin-top: 16px;
}

.kb-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

/* 纯 CSS spinner — 零外部依赖，首帧直接渲染 */
.kb-loading {
  text-align: center;
  padding: 80px 0;

  p {
    margin-top: 12px;
    color: var(--color-text-secondary);
  }
}

.kb-spinner {
  display: inline-block;
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: kb-spin 0.7s linear infinite;
}

@keyframes kb-spin {
  to { transform: rotate(360deg); }
}
</style>
