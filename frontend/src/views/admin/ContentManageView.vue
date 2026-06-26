<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getContentListApi } from '@/api/admin'

const activeTab = ref('questions')
const loading = ref(false)

const contentData = ref({
  questions: [],
  shadow: [],
  materials: [],
  dubbing: [],
})

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

onMounted(() => { loadContent(activeTab.value) })

watch(activeTab, (tab) => { loadContent(tab) })

async function loadContent(type) {
  if (contentData.value[type]?.length > 0) return // 已加载
  loading.value = true
  try {
    const res = await getContentListApi(type)
    contentData.value[type] = res.items || []
  } catch {
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">内容管理</h2>
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
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
