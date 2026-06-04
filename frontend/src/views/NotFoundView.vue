<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="flex-center" style="height: 100vh; flex-direction: column; gap: 16px;">
    <el-result
      icon="warning"
      title="404"
      sub-title="页面不存在，请检查链接是否正确"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/home')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>
