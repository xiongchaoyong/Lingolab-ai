<script setup>
import { ref } from 'vue'

const activeTab = ref('questions')

// 题库
const questions = ref([
  { id: 1, content: 'What does the woman mean?', type: '听力', difficulty: 'B1', dimension: '听力' },
  { id: 2, content: 'Describe your favorite food', type: '口语', difficulty: 'B1', dimension: '口语' },
  { id: 3, content: 'Choose the best word to fill...', type: '阅读', difficulty: 'B1', dimension: '阅读' },
])

// 跟读内容
const shadowContents = ref([
  { id: 1, word: 'restaurant', ipa: '/ˈres.trɒnt/', difficulty: 'A2', type: '单词' },
  { id: 2, word: 'I like to play football.', ipa: '', difficulty: 'A1', type: '句子' },
])

// 推荐资料
const materials = ref([
  { id: 1, title: 'Master English TH Sound', type: '视频', category: '发音', level: 'B1' },
  { id: 2, title: 'The History of English', type: '文章', category: '阅读', level: 'B1' },
])

// 配音片段
const dubbingClips = ref([
  { id: 1, title: 'Toy Story', line: 'To infinity and beyond!', difficulty: '简单' },
])

const tabs = [
  { name: 'questions', label: '测评题库' },
  { name: 'shadow', label: '跟读内容' },
  { name: 'materials', label: '推荐资料' },
  { name: 'dubbing', label: '配音片段' },
]

const dataMap = { questions, shadow: shadowContents, materials, dubbing: dubbingClips }

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
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">内容管理</h2>
      <el-button type="primary" :icon="Plus">新增</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name">
        <el-table :data="dataMap[tab.name]" stripe>
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
          <el-table-column label="操作" width="160">
            <template #default>
              <el-button size="small" text type="primary">编辑</el-button>
              <el-button size="small" text type="danger">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
