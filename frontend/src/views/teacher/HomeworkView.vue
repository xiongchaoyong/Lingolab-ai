<script setup>
import { ref } from 'vue'

const homeworks = ref([
  { id: 1, title: 'Unit 3 跟读练习', class: '初级英语A班', type: '跟读', assignedAt: '6月2日', dueAt: '6月5日', completed: 10, total: 12 },
  { id: 2, title: '餐厅场景对话', class: '中级口语B班', type: '对话', assignedAt: '6月1日', dueAt: '6月4日', completed: 6, total: 8 },
])

const showAssignDialog = ref(false)
const newHomework = ref({ title: '', class: '', type: '跟读', dueAt: '', description: '' })

function assignHomework() {
  homeworks.value.unshift({
    id: Date.now(), title: newHomework.value.title, class: newHomework.value.class,
    type: newHomework.value.type, assignedAt: new Date().toISOString().slice(0, 5).replace('-', '月').replace('-', '日'),
    dueAt: newHomework.value.dueAt, completed: 0, total: 12,
  })
  showAssignDialog.value = false
  newHomework.value = { title: '', class: '', type: '跟读', dueAt: '', description: '' }
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">作业管理</h2>
      <el-button type="primary" :icon="Plus" @click="showAssignDialog = true">布置作业</el-button>
    </div>

    <el-table :data="homeworks" stripe>
      <el-table-column prop="title" label="作业标题" />
      <el-table-column prop="class" label="班级" width="140" />
      <el-table-column prop="type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.type === '跟读' ? 'primary' : 'success'">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assignedAt" label="布置时间" width="100" />
      <el-table-column prop="dueAt" label="截止" width="100" />
      <el-table-column label="完成" width="120">
        <template #default="{ row }">
          <el-progress :percentage="Math.round(row.completed / row.total * 100)" :stroke-width="6" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default>
          <el-button size="small" text type="primary">查看提交</el-button>
          <el-button size="small" text>编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAssignDialog" title="布置作业" width="480px">
      <el-form label-position="top">
        <el-form-item label="作业标题">
          <el-input v-model="newHomework.title" placeholder="如：Unit 3 跟读练习" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="newHomework.class" style="width:100%">
            <el-option label="初级英语A班" value="初级英语A班" />
            <el-option label="中级口语B班" value="中级口语B班" />
          </el-select>
        </el-form-item>
        <el-form-item label="作业类型">
          <el-radio-group v-model="newHomework.type">
            <el-radio value="跟读">跟读练习</el-radio>
            <el-radio value="对话">场景对话</el-radio>
            <el-radio value="配音">配音挑战</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="newHomework.dueAt" type="date" style="width:100%" />
        </el-form-item>
        <el-form-item label="作业说明">
          <el-input v-model="newHomework.description" type="textarea" :rows="3" placeholder="具体要求和说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="assignHomework" :disabled="!newHomework.title">布置</el-button>
      </template>
    </el-dialog>
  </div>
</template>
