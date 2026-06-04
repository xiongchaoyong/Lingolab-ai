<script setup>
import { ref } from 'vue'

const classes = ref([
  { id: 1, name: '初级英语A班', level: 'A1-A2', students: 12, inviteCode: 'LINGO-A001', createdAt: '2026-05-20' },
  { id: 2, name: '中级口语B班', level: 'B1-B2', students: 8, inviteCode: 'LINGO-B003', createdAt: '2026-06-01' },
])

const showCreateDialog = ref(false)
const newClass = ref({ name: '', description: '', levelRange: 'A1-A2' })

function createClass() {
  classes.value.push({
    id: Date.now(), name: newClass.value.name, level: newClass.value.levelRange,
    students: 0, inviteCode: 'LINGO-' + Math.random().toString(36).slice(2, 6).toUpperCase(),
    createdAt: new Date().toISOString().slice(0, 10),
  })
  showCreateDialog.value = false
  newClass.value = { name: '', description: '', levelRange: 'A1-A2' }
}
</script>

<template>
  <div class="content-card">
    <div class="flex-between" style="margin-bottom: var(--spacing-xl);">
      <h2 class="page-title" style="margin-bottom:0;">班级管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">创建班级</el-button>
    </div>

    <el-table :data="classes" stripe>
      <el-table-column prop="name" label="班级名称" />
      <el-table-column prop="level" label="等级范围" width="100" />
      <el-table-column prop="students" label="学生数" width="80" />
      <el-table-column prop="inviteCode" label="邀请码" width="140">
        <template #default="{ row }">
          <el-tag type="success">{{ row.inviteCode }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="120" />
      <el-table-column label="操作" width="180">
        <template #default>
          <el-button size="small" text type="primary">查看学生</el-button>
          <el-button size="small" text type="danger">解散</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="classes.length === 0" description="暂无班级，创建班级并分享邀请码给学生加入" />

    <el-dialog v-model="showCreateDialog" title="创建班级" width="440px">
      <el-form label-position="top">
        <el-form-item label="班级名称">
          <el-input v-model="newClass.name" placeholder="如：初级英语A班" />
        </el-form-item>
        <el-form-item label="等级范围">
          <el-select v-model="newClass.levelRange" style="width:100%">
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
        <el-button type="primary" @click="createClass" :disabled="!newClass.name">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
